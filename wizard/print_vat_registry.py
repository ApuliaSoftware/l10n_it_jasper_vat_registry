# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia Software S.r.l. (<info@apuliasoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields, osv, orm
from tools.translate import _
import time


class temporay_vatregisty_total(orm.Model):

    _name = "temporay.vatregisty.total"

    _columns = {
        'tax_id': fields.many2one('account.tax', 'Tax ID'),
        'amount_untaxed': fields.float('Amount Untaxed'),
        'amount_tax': fields.float('Amount Tax'),
        'amount_tax_indet': fields.float('Amount Tax Indet'),
        'amount_tax_split': fields.float('Amount Tax Split'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'period_id': fields.many2one('account.period', 'Period'),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Account'),
        }

    def _pulisci(self, cr, uid, context):
        ids = self.search(cr, uid, [])
        self.unlink(cr, uid, ids, context)
        return True

    def load_data(self, cr, uid, ids, context=None):
        self._pulisci(cr, uid, context)
        if not ids:
            return False
        group_dict = {}
        for line in self.pool.get('temporary.vatregistry').browse(
                cr, uid, ids, context):
            # if not line.period_id.id in group_dict:
            #     group_dict.update({line.period_id.id: {}})
            # if not line.journal_id.id in group_dict[line.period_id.id]:
            #     group_dict[line.period_id.id].update(
            #         {line.journal_id.id: {}})
            # in questo crea il totale della stampa
            if not line.tax_code_id.id in group_dict:
                # [
                #     line.period_id.id][line.journal_id.id]:
                group_dict.update({
                    line.tax_code_id.id: {
                        'amount_untaxed': 0.0,
                        'amount_tax': 0.0,
                        'amount_tax_indet':0.0,
                        'amount_tax_split': 0.0
                    }})
            group_dict[
                line.tax_code_id.id]['amount_untaxed'] += line.amount_untaxed
            if line.tax_code_id.iva_indet:
                group_dict[
                    line.tax_code_id.id]['amount_tax_indet'] += line.amount_tax
            else:
                group_dict[
                    line.tax_code_id.id]['amount_tax'] += line.amount_tax
        #
        # for period_id, journals in group_dict.iteritems():
        #     for journal_id, taxes in journals.iteritems():
        for tax_code_id, amounts in group_dict.iteritems():
                    self.create(cr, uid, {
                        'tax_code_id': tax_code_id,
                        'amount_untaxed': amounts['amount_untaxed'],
                        'amount_tax': amounts['amount_tax'],
                        'amount_tax_indet': amounts['amount_tax_indet'],
                        'amount_tax_split': amounts['amount_tax_split'],
                        # 'journal_id': journal_id,
                        # 'period_id': period_id,
                        }, context)
        return True


class temporary_vatregistry(orm.Model):

    _name = 'temporary.vatregistry'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company'),
        'name': fields.char('Number', size=64),
        'date': fields.date('Date'),
        'invoice_number': fields.char('Invoice Number', size=64),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID'),
        'invoice_date': fields.date('Invoice Date'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'invoice_type': fields.char('Invoice Type', size=64),
        'invoice_total': fields.float('Invoice Total'),
        'tax_id': fields.many2one('account.tax', 'Tax ID'),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Account'),
        'amount_untaxed': fields.float('Amount Untaxed'),
        'amount_tax': fields.float('Amount Tax'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'period_id': fields.many2one('account.period', 'Period'),
        'registry_id': fields.many2one('vat.registry', 'Registro Iva'),
        'name_registry': fields.char('Descrizione Registro', size=30),
        'code_registry': fields.char('Codice Registro', size=10),
        'order': fields.char('Ordine di Stampa', size=256),
                }

    def _pulisci(self, cr, uid, context):
        ids = self.search(cr, uid, [])
        self.unlink(cr, uid, ids, context)
        return True

    def load_data(self, cr, uid, ids, paramters, context=None):
        self._pulisci(cr, uid, context)
        #~ move_obj = self.pool.get('account.move')
        invoice_obj = self.pool.get('account.invoice')
        curr_obj = self.pool['res.currency']

        #~ move_ids = move_obj.search(cr, uid, [
            #~ ('journal_id', 'in', [j.id for j in paramters.journal_ids]),
            #~ ('period_id', 'in', [p.id for p in paramters.period_ids]),
            #~ ('state', '=', 'posted'),
            #~ ], order='date')
        invoice_ids = invoice_obj.search(cr, uid, [
            ('journal_id', 'in', [j.id for j in paramters.journal_ids]),
            ('period_id', 'in', [p.id for p in paramters.period_ids]),
            ('state', 'not in', ('posted', 'draft',
                                 'cancel', 'proforma', 'proforma2')),
            ], order='registration_date')
        if not invoice_ids:
            #~ TODO
            return False
        line_ids = []
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
            std_curr = self.pool['res.company'].browse(
                cr, uid, invoice.company_id.id).currency_id.id
            tax_sign = 1
            if invoice.state in ('proforma', 'proforma2'):
                continue
            invoice_number = invoice.origin or invoice.number
            if invoice.company_id.use_origin:
                invoice_number = invoice.origin
            if invoice.type in ('in_refund', 'out_refund'):
                tax_sign = -1
            if invoice.type in ('in_refund', 'in_invoice'):
                invoice_number = invoice.supplier_invoice_number
            inv_total = curr_obj.compute(
                 cr, uid, invoice.currency_id.id,
                 std_curr, invoice.amount_total, True, False, False, context)
            for tax_line in invoice.tax_line:
                amount_untaxed = curr_obj.compute(
                    cr, uid, invoice.currency_id.id, std_curr,
                    tax_line.base, True, False, False, context)
                tax_code = tax_line.tax_code_id
                if not tax_code:
                    raise orm.except_orm(
                        'Errore',
                        'Controllare la Fattura '+ invoice.number)
                if tax_code.perc_indet <> 0.0:
                    if tax_code.iva_indet:
                        amount_untaxed = (amount_untaxed * tax_code.perc_indet / 100)
                    else:
                        amount_untaxed = (amount_untaxed *
                                              (100 - tax_code.perc_indet) / 100)
                amount_tax = curr_obj.compute(
                    cr, uid, invoice.currency_id.id, std_curr,
                    tax_line.amount, True, False, False, context)
                order = ''
                if invoice.type in ('in_refund', 'in_invoice'):
                    order= invoice.registration_date+' '+invoice.move_id.name
                else:
                    order = invoice.date_invoice + ' ' + invoice_number
                vals = {
                    'company_id': invoice.company_id.id,
                    'name': invoice.move_id.name,
                    'date': invoice.registration_date,
                    'invoice_number': invoice_number,
                    'invoice_id': invoice.id,
                    'invoice_date': invoice.date_invoice,
                    'partner_id': invoice.partner_id.id,
                    'invoice_type': invoice.type,
                    'invoice_total': inv_total,
                    'tax_code_id': tax_line.tax_code_id.id,
                    'amount_untaxed': amount_untaxed * tax_sign,
                    'amount_tax': amount_tax * tax_sign,
                    'journal_id': invoice.journal_id.id,
                    'period_id': invoice.period_id.id,
                    'registry_id': paramters.registry_id.id,
                    'name_registry': paramters.registry_id.name,
                    'code_registry': paramters.registry_id.reg_vat_code,
                    'order': order,
                }

                line_ids.append(self.create(cr, uid, vals, context))
        ok = self.pool.get('temporay.vatregisty.total').load_data(
            cr, uid, line_ids, context)
        if not ok:
            raise osv.except_osv(_('Error!'), _('Failed to load data'))
        return True


class wizard_print_vatregistry(orm.TransientModel):

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(
            cr, uid, context=ctx)
        return period_ids

    _name = "wizard.print.vatregistry"

    _columns = {
        'period_ids': fields.many2many(
            'account.period',
            'vat_registry_periods_rel', 'period_id', 'registro_id',
            'Periods',
            help='Select periods you want retrieve documents from',
            required=True),
        'type': fields.selection([
            ('customer', 'Customer Invoices'),
            ('supplier', 'Supplier Invoices'),
            ('corrispettivi', 'Corrispettivi'),
            ], 'Layout', required=True),
        'registry_id': fields.many2one('vat.registry', 'Registro Iva'),
        'journal_ids': fields.many2many(
            'account.journal',
            'vat_registry_journals_rel',
            'journal_id',
            'registro_id',
            'Journals',
            help='Select journals you want retrieve documents from',
            required=True),
        'message': fields.char('Message', size=64, readonly=True),
        'fiscal_page_base': fields.integer('Last printed page', required=True),
        'fiscal_year_page': fields.char('Anno di Stampa',
                                        size=4, required=True),
        }

    _defaults = {
        'type': 'customer',
        'period_ids': _get_period,
        'fiscal_page_base': 0,
        'fiscal_year_page': lambda * a: time.strftime('%Y')
        }


    def on_change_registry_id(self, cr, uid, ids, registry_id, context=False):
        v = {}
        # import pdb;pdb.set_trace()
        warning = {}
        domain = {}
        if not context:
            context = {}
        if registry_id:
            registry = self.pool.get('vat.registry').browse(cr, uid, registry_id)
            if registry.journal_ids:
                iids =[]
                for journal in registry.journal_ids:
                    iids.append(journal.journal_id.id)
                v = {'journal_ids' : [(6, 0, iids)]}
        return {'value': v, 'domain': domain, 'warning': warning}



    def start_printing(self, cr, uid, ids, context={}):
        parameters = self.browse(cr, uid, ids, context)[0]
        ok = self.pool.get('temporary.vatregistry').load_data(
            cr, uid, ids, parameters, context)
        if ok:
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['form'] = {}
            data['form'][
                'parameters'] = {'last_page': parameters.fiscal_page_base,
                                 'last_year': parameters.fiscal_year_page,
                                 }
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'vat_jr_registry',
                    'datas': data,
                    }
        else:
            raise osv.except_osv(_('Error !'), _('Nothing To Print'))
        return {'type': 'ir.actions.act_window_close'}
