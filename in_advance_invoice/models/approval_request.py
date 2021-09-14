from odoo import api, fields, models, _


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    account_move_id = fields.Many2one('account.move', string='Account move', compute='_compute_value')

    def _compute_value(self):
        for rec in self:
            rec.account_move_id = self.env['account.move'].search([('approval_request_id', '=', rec.id)])

    def action_approve(self, approver=None):
        self.account_move_id.write({'state': 'approved'})
        return super().action_approve(approver)

    def action_cancel(self):
        self.account_move_id.write({'state': 'cancel'})
        return super().action_cancel()

    def action_refuse(self, approver=None):
        self.account_move_id.write({'state': 'draft'})
        return super().action_refuse(approver)

    def action_draft(self):
        self.account_move_id.write({'state': 'draft'})
        return super().action_draft()
