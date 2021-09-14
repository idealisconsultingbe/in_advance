from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AgoAddendum(models.Model):
    _name = 'ago.addendum'
    _description = 'Agoria Addendum'
    _order = 'sequence'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=99)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.user.company_id
    )
    ir_act_report_id = fields.Many2one('ir.actions.report', string='Report', required=True)
    model = fields.Char('Model', related='ir_act_report_id.model', store=True)
    addendum = fields.Binary('Addendum', required=True)
    fname_addendum = fields.Char('Addendum Filename')
    condition = fields.Selection(
        [('always', 'Always'), ('domain', 'Domain'), ('advanced_domain', 'Advanced Domain')],
        default='always',
        required=True,
    )
    position = fields.Selection([('top', 'Top'), ('bottom', 'Bottom')], default='bottom', required=True)
    filter_domain = fields.Char('Domain', default='[]')

    def open_generate_filter_domain_wizard(self):
        self.ensure_one()

        if not self.model:
            raise ValidationError(_('Please select a model before generate a domain'))

        is_simplified_domain = self.condition == 'domain'
        return self.env['advanced.domain.generator'].open_wizard(
            self, self.model, is_simplified_domain=is_simplified_domain
        )
