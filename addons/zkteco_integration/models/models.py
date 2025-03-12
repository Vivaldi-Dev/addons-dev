# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.safe_eval import pytz


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


    def script_time_att(self):
        # Obtener la zona horaria de África/Maputo
        tz_maputo = pytz.timezone("Africa/Maputo")
        utc = pytz.utc

        # Conectar a la base de datos

        # Buscar todas las asistencias con check_in y check_out
        attendances = self['hr.attendance'].search([('check_in', '!=', False), ('check_out', '!=', False)])

        for attendance in attendances:
            # Convertir check_in a África/Maputo
            if attendance.check_in:
                check_in_utc = attendance.check_in.replace(tzinfo=utc)
                check_in_maputo = check_in_utc.astimezone(tz_maputo)
                attendance.write({'check_in':check_in_maputo})

            # Convertir check_out a África/Maputo
            if attendance.check_out:
                check_out_utc = attendance.check_out.replace(tzinfo=utc)
                check_out_maputo = check_out_utc.astimezone(tz_maputo)
                attendance.write({'check_out': check_out_maputo})


class ZkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char(string='Número de série', required=True)
    address_id = fields.Many2one('res.partner', string='Endereço de Trabalho')
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.user.company_id.id)
