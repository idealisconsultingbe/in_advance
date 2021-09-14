from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    construction_site_concerned = fields.Char(string='Site concerned')
    introductory_sentence = fields.Char(string='Introductory sentence')
    account_number = fields.Char(string='Account number')
    cumulative_amount = fields.Monetary(currency_field='currency_id', string='Cumulative amount')
    previous_amount = fields.Monetary(currency_field='currency_id', string='Previous amount')
    cumulative_statement = fields.Monetary(currency_field='currency_id', string='Cumulative statement')
    previous_statement = fields.Monetary(currency_field='currency_id', string='Previous statement')
    monthly_progress = fields.Monetary(compute='_compute_values', currency_field='currency_id',
                                       string='Monthly progress', readonly=True)
    cumulative_deduction_deposit = fields.Monetary(currency_field='currency_id',
                                                   string='Cumulative deduction of the deposit')
    previous_deduction_deposit = fields.Monetary(currency_field='currency_id',
                                                 string='Previous deduction from the deposit')
    net_amount = fields.Monetary(compute='_compute_values', currency_field='currency_id', string='Net amount',
                                 readonly=True)
    revision = fields.Monetary(currency_field='currency_id', string='Revision')
    revision_amount_included = fields.Monetary(compute='_compute_values', currency_field='currency_id',
                                               string='Revision amount included', readonly=True)
    amount_deposit_deducted = fields.Monetary(compute='_compute_values', currency_field='currency_id',
                                              string='Amount of the deposit deducted', readonly=True)
    approval_request_id = fields.Many2one('approval.request', string='Approval request', readonly=True)
    imp_site = fields.Char(string='Imputation chantier')
    auto_liquidation = fields.Selection([
        ('autoliquidation', '"En auto-liquidation A.R. n°1, article 20"'), 
        ('exoneration_tva', 'Exonération de TVA suivant l\'article 44 du code TVA Belgique')], string="En auto liquidation", default='autoliquidation')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('pending_approval', 'Pending approval'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    # state = fields.Selection(selection_add=[
    #     ('pending_approval', 'Pending approval'),
    #     ('approved', 'Approved'),
    # ], ondelete={
    #     'pending_approval': 'set default',
    #     'approved': 'set default',
    # })

    def in_amount_to_text(self, amount):
        return self.partner_id.currency_id.amount_to_text(amount)

    def action_state_pending_approval(self):
        self.write({'state': 'pending_approval'})
        self.approval_request_id.action_withdraw()

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        category = self.env.ref('in_advance_invoice.approval_category_approve_invoice')
        res.approval_request_id = self.env['approval.request'].create({
            'name': 'Invoice validation',
            'category_id': category.id,
            'request_status': 'pending',
            'date_start': fields.Datetime.now(),
            'date_end': fields.Datetime.now(),
        })
        res.approval_request_id._onchange_category_id()
        return res

    def _compute_values(self):
        for amount in self:
            if amount.cumulative_amount and amount.previous_amount and not amount.cumulative_statement and not amount.previous_statement:
                amount.monthly_progress = amount.cumulative_amount - amount.previous_amount
            elif not amount.cumulative_amount and not amount.previous_amount and amount.cumulative_statement and amount.previous_statement:
                amount.monthly_progress = amount.cumulative_statement - amount.previous_statement
            else:
                amount.monthly_progress = (amount.cumulative_amount - amount.previous_amount) + (
                        amount.cumulative_statement - amount.previous_statement)
            if amount.cumulative_deduction_deposit and amount.previous_deduction_deposit:
                amount.amount_deposit_deducted = amount.cumulative_deduction_deposit + amount.previous_deduction_deposit
            else:
                amount.amount_deposit_deducted = 0
            amount.net_amount = amount.monthly_progress + amount.amount_deposit_deducted
            amount.revision_amount_included = amount.net_amount + amount.revision
