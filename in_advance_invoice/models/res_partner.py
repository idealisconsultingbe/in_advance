from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    denomination = fields.Text(string='Denomination')
    ###----- invoicing_mails is a text field ---- ###
    invoicing_mails = fields.Text(string='Invoicing mails')


class ResCompany(models.Model):
    _inherit = 'res.company'

    fax = fields.Char(string='Fax')
