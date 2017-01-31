# -*- coding: utf-8 -*-
# (c) 2016 Alfredo de la Fuente - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import openerp.tests.common as common
from openerp import exceptions


class TestSaleOrderCreateEventHour(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderCreateEventHour, self).setUp()
        self.task_model = self.env['project.task']
        self.sale_model = self.env['sale.order']
        self.account_model = self.env['account.analytic.account']
        self.project_model = self.env['project.project']
        self.event_model = self.env['event.event']
        self.task_model = self.env['project.task']
        self.procurement_model = self.env['procurement.order']
        self.wiz_add_model = self.env['wiz.event.append.assistant']
        self.wiz_del_model = self.env['wiz.event.delete.assistant']
        self.type_hour_model = self.env['hr.type.hour'].with_context(
            check_write_type_hour=True)
        self.sunday = self.browse_ref(
            'sale_order_create_event_hour.type_hour_sunday').with_context(
            check_write_type_hour=True)
        self.contract_model = self.env['hr.contract']
        self.wiz_model = self.env['wiz.calculate.workable.festive']
        self.employee = self.env.ref('hr.employee')
        self.employee.address_home_id = self.env.ref('base.res_partner_26').id
        contract_vals = {
            'name': 'Contract 1',
            'employee_id': self.employee.id,
            'partner': self.ref('base.res_partner_26'),
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'wage': 500,
            'date_start': '2016-01-02'}
        self.contract = self.contract_model.create(contract_vals)
        wiz = self.wiz_model.with_context(
            {'active_id': self.contract.id}).create({'year': 2016})
        wiz.with_context(
            {'active_id':
             self.contract.id}).button_calculate_workables_and_festives()
        account_vals = {'name': 'account procurement service project',
                        'date_start': '2016-01-15 00:00:00',
                        'start_time': 5.0,
                        'end_time': 10.0,
                        'date': '2016-02-28 00:00:00',
                        'use_tasks': True}
        self.account = self.account_model.create(account_vals)
        self.project = self.env['project.project'].search(
            [('analytic_account_id', '=', self.account.id)], limit=1)[:1]
        service_product = self.env.ref('product.product_product_consultant')
        service_product.write({'performance': 5.0,
                               'recurring_service': True})
        service_product.performance = 5.0
        service_product.route_ids = [
            (6, 0,
             [self.ref('procurement_service_project.route_serv_project')])]
        sale_vals = {
            'name': 'sale order 1',
            'partner_id': self.ref('base.res_partner_1'),
            'partner_shipping_id': self.ref('base.res_partner_1'),
            'partner_invoice_id': self.ref('base.res_partner_1'),
            'pricelist_id': self.env.ref('product.list0').id,
            'project_id': self.account.id,
            'project_by_task': 'no'}
        sale_line_vals = {
            'product_id': service_product.id,
            'name': service_product.name,
            'start_date': '2016-01-15',
            'start_hour': 5.0,
            'end_hour': 10.0,
            'end_date': '2016-02-28',
            'product_uom_qty': 7,
            'product_uos_qty': 7,
            'product_uom': service_product.uom_id.id,
            'price_unit': service_product.list_price,
            'performance': 5.0,
            'january': True,
            'february': True,
            'week4': True,
            'week5': True,
            'tuesday': True,
            'thursday': True}
        sale_vals['order_line'] = [(0, 0, sale_line_vals)]
        self.sale_order = self.sale_model.create(sale_vals)

    def test_disabled_editing_module_type_hour(self):
        with self.assertRaises(exceptions.Warning):
            self.sunday.name = 'SUNDAY'
        with self.assertRaises(exceptions.Warning):
            self.sunday.unlink()

    def test_type_hour(self):
        hour_type = self.type_hour_model.create({
            'name': 'Test',
        })
        hour_type.name = 'New Name'
        hour_type.unlink()

    def test_sale_order_create_event_hour(self):
        self.project.write({
            'type_hour':
                self.ref('sale_order_create_event_hour.type_hour_working'),
        })
        self.sale_order.order_line.write({'sunday': True})
        self.sale_order.action_button_confirm()
        self.project.tasks[0].show_sessions_from_task()
        self.project.tasks[0].button_recalculate_sessions()
        cond = [('project_id', '=', self.project.id)]
        event = self.event_model.search(cond, limit=1)
        wiz_vals = {'min_event': event.id,
                    'max_event': event.id,
                    'min_from_date': '2016-01-15 00:00:00',
                    'max_to_date': '2016-02-28 00:00:00',
                    'from_date': '2016-01-15 00:00:00',
                    'to_date': '2016-02-28 00:00:00',
                    'partner': self.env.ref('base.res_partner_26').id}
        wiz = self.wiz_add_model.with_context(
            {'active_ids': [event.id]}).create(wiz_vals)
        wiz.with_context({'active_ids': [event.id]}).action_append()
        wiz._compute_update_registration_start_date(event.registration_ids[0])
        wiz._compute_update_registration_end_date(event.registration_ids[0])
        wiz._update_registration_start_date(event.registration_ids[0])
        wiz._update_registration_date_end(event.registration_ids[0])
        wiz.from_date = '2016-05-01'
        wiz.onchange_dates_and_partner()
        wiz.write({'from_date': '2016-01-20',
                   'to_date': '2016-01-15'})
        wiz.onchange_dates_and_partner()
        wiz.write({'from_date': '2016-01-01',
                   'min_from_date': '2016-01-15'})
        wiz.onchange_dates_and_partner()
        wiz.write({'from_date': '2016-05-01',
                   'max_to_date': '2016-02-28'})
        wiz.onchange_dates_and_partner()
        wiz.write({'from_date': '2016-05-01',
                   'max_to_date': '2016-02-25'})
        wiz.onchange_dates_and_partner()
        wiz.write({'to_date': '2016-01-13',
                   'min_from_date': '2016-01-15'})
        wiz.onchange_dates_and_partner()
        wiz.write({'to_date': '2016-03-01',
                   'max_to_date': '2016-02-28'})
        wiz.onchange_dates_and_partner()
        wiz_vals = {'min_event': event.id,
                    'max_event': event.id,
                    'min_from_date': '2016-01-15 00:00:00',
                    'max_to_date': '2016-02-28 00:00:00',
                    'from_date': '2016-01-15 00:00:00',
                    'to_date': '2016-02-28 00:00:00',
                    'partner': self.env.ref('base.res_partner_26').id}
        wiz.write(wiz_vals)
        wiz.onchange_dates_and_partner()
        wiz_vals.update({'removal_date': '2025-12-01',
                         'notes': 'Registration canceled by system'})
        wiz = self.wiz_del_model.create(wiz_vals)
        vals = ['max_event', 'max_to_date', 'min_from_date', 'min_event',
                'past_sessions', 'start_time', 'from_date', 'later_sessions',
                'to_date', 'partner', 'message', 'end_time']
        wiz.with_context(
            {'active_ids': [event.id]}).default_get(vals)
        wiz.from_date = '2016-05-01'
        wiz._dates_control()
        wiz.write({'from_date': '2016-01-20',
                   'to_date': '2016-01-15'})
        wiz._dates_control()
        wiz.write({'from_date': '2016-01-01',
                   'min_from_date': '2016-01-15'})
        wiz._dates_control()
        wiz.write({'min_from_date': '2016-01-15 00:00:00',
                   'max_to_date': '2016-02-20 00:00:00',
                   'from_date': '2016-02-21 00:00:00',
                   'to_date': '2016-02-28 00:00:00'})
        wiz._dates_control()
        wiz.write({'min_from_date': '2016-02-20 00:00:00',
                   'max_to_date': '2016-02-28 00:00:00',
                   'from_date': '2016-01-15 00:00:00',
                   'to_date': '2016-02-10 00:00:00'})
        wiz._dates_control()
        wiz.write({'min_from_date': '2016-01-15 00:00:00',
                   'max_to_date': '2016-02-20 00:00:00',
                   'from_date': '2016-01-15 00:00:00',
                   'to_date': '2016-02-15 00:00:00'})
        wiz._dates_control()
        wiz.write({'min_from_date': '2016-01-15 00:00:00',
                   'max_to_date': '2016-02-20 00:00:00',
                   'from_date': '2016-01-15 00:00:00',
                   'to_date': '2016-02-21 00:00:00'})
        wiz._dates_control()
        wiz._prepare_dates_for_search_registrations()
        wiz_vals = {'min_event': event.id,
                    'max_event': event.id,
                    'min_from_date': '2016-01-15 00:00:00',
                    'max_to_date': '2016-02-28 00:00:00',
                    'from_date': '2016-01-15 00:00:00',
                    'to_date': '2016-02-28 00:00:00',
                    'removal_date': '2025-12-01',
                    'notes': 'Registration canceled by system',
                    'partner': self.env.ref('base.res_partner_26').id}
        wiz.write(wiz_vals)
        wiz.with_context(
            {'active_ids': [event.id]}).action_delete()
        event.registration_ids[0].with_context(
            {'event_id': event.id}).button_registration_open()
        event.registration_ids[0].button_reg_cancel()
        self.assertNotEqual(
            len(self.project.tasks[0].sessions), 0,
            'Sessions no generated')
        event.registration_ids[0].state = 'open'
        wiz_vals = {'min_event': event.id,
                    'max_event': event.id,
                    'registration': event.registration_ids[0].id,
                    'min_from_date': '2016-01-15 00:00:00',
                    'max_to_date': '2016-02-28 00:00:00',
                    'from_date': '2016-01-15 00:00:00',
                    'to_date': '2016-02-28 00:00:00',
                    'partner': self.env.ref('base.res_partner_26').id}
        wiz.write(wiz_vals)
        event.registration_ids[0].with_context(
            {'event_id': event.id}).button_registration_open()
        event.registration_ids[0].button_reg_cancel()
