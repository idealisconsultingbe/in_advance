import base64
import io

from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class AgoIrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """
        Inherit the method _post_pdf to add addendums in the content. The main method will split the content
        by res_id and add (if required) the generated document in attachments.

        Odoo will use the tag /Root/Dest (created by wkhtmltopdf) to know how to cut the PDF content
        by document (res_id). It means that if we simply add some pages, the value of the tag will no longer be right.
        To avoid to modify tags in the PDF content, we simply split the document by res_id
        and call the main method (super) record by record.
        """
        if not pdf_content or not res_ids:
            return super()._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

        addendums = self.env['ago.addendum'].search([('ir_act_report_id', '=', self.id)])

        if not addendums:
            return super()._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

        # Evaluate the domain of each addendum
        res_ids_by_addendum = {}
        for addendum in addendums:
            if addendum.condition == 'always':
                res_ids_by_addendum[addendum] = res_ids
            else:
                domain = safe_eval(addendum.filter_domain) + [('id', 'in', res_ids)]
                res_ids_by_addendum[addendum] = self.env[self.model].search(domain).ids

        pdf_content_stream = io.BytesIO(pdf_content)
        reader = PdfFileReader(pdf_content_stream)

        # Read the PDF to be able to cut the PDF (copy past of the main method)
        streams = []
        if len(res_ids) == 1:
            streams.append((res_ids[0], pdf_content_stream))
        else:
            root = reader.trailer['/Root']
            if '/Outlines' in root and '/First' in root['/Outlines']:
                outlines_pages = []
                node = root['/Outlines']['/First']
                while True:
                    outlines_pages.append(root['/Dests'][node['/Dest']][0])
                    if '/Next' not in node:
                        break
                    node = node['/Next']
                outlines_pages = sorted(set(outlines_pages))
                # There should be only one top-level heading by document
                assert len(outlines_pages) == len(res_ids)
                # There should be a top-level heading on first page
                assert outlines_pages[0] == 0
                for i, num in enumerate(outlines_pages):
                    to = outlines_pages[i + 1] if i + 1 < len(outlines_pages) else reader.numPages
                    attachment_writer = PdfFileWriter()
                    for j in range(num, to):
                        attachment_writer.addPage(reader.getPage(j))
                    stream = io.BytesIO()
                    attachment_writer.write(stream)
                    streams.append((res_ids[i], stream))
            else:
                # If no outlines available, do not save each record
                streams.append((None, pdf_content_stream))

        # Create the main PDF merger (contains all documents)
        full_pdf_merger = PdfFileMerger()
        # Look on all streams (a stream is a document for a res_id)
        for res_id, stream in streams:
            pdf_merger = PdfFileMerger()

            for addendum in addendums.filtered(lambda line: line.position == 'top'):
                # Append the addendum in the stream if required
                if res_id not in res_ids_by_addendum[addendum]:
                    continue

                pdf_addendum_content = io.BytesIO(base64.b64decode(addendum.addendum))
                pdf_addendum_reader = PdfFileReader(pdf_addendum_content)
                pdf_merger.append(pdf_addendum_reader)

            pdf_reader = PdfFileReader(stream)
            pdf_merger.append(pdf_reader, import_bookmarks=False)

            for addendum in addendums.filtered(lambda line: line.position == 'bottom'):
                # Append the addendum in the stream if required
                if res_id not in res_ids_by_addendum[addendum]:
                    continue

                pdf_addendum_content = io.BytesIO(base64.b64decode(addendum.addendum))
                pdf_addendum_reader = PdfFileReader(pdf_addendum_content)
                pdf_merger.append(pdf_addendum_reader)

            # Retrieve the PDF content for the current document
            pdf_merger.write(stream)
            record_pdf_content = stream.getvalue()
            try:
                stream.close()
            except Exception:
                pass

            # Call the method super with ONLY the current res_id and his PDF content.
            # This method return the content of the PDF. The content can change during the call
            new_pdf_content = super()._post_pdf(save_in_attachment, pdf_content=record_pdf_content, res_ids=[res_id])

            # We recreate a new PDF with the new content
            new_reader_buffer = io.BytesIO(new_pdf_content)
            new_reader = PdfFileReader(new_reader_buffer)

            # Add the PDF content to the main PDF merger
            full_pdf_merger.append(new_reader)

        # Generate the content of the main PDF
        full_pdf = io.BytesIO()
        full_pdf_merger.write(full_pdf)
        pdf_content = full_pdf.getvalue()
        full_pdf.close()

        return pdf_content
