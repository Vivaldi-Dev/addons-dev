# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_id = fields.Char(string='ID do Dispositivo Biométrico')

class Attendance(models.Model):
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """overriding the __check_validity function for employee attendance."""
        pass

    device_id = fields.Char(string='Biometric Device ID')
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out')],
                                  string='Punching Type')

    attendance_type = fields.Selection([('1', 'Finger'),
                                        ('15', 'Face'),
                                        ('2','Type_2'),
                                        ('25','Palm'),
                                        ('3','Password'),
                                        ('4','Card')], string='Category')
    punching_time = fields.Datetime(string='Punching Time')
    address_id = fields.Many2one('res.partner', string='Working Address')


class ZkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char(string='Número de série', required=True)
    address_id = fields.Many2one('res.partner', string='Endereço de Trabalho')
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.user.company_id.id)
