from odoo import _, api, exceptions, fields, models
from odoo.addons.bus.models.bus import channel_with_db, json_dump
from odoo.addons.web.controllers.main import clean_action

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"


class AttendanceNotification(models.Model):
    _name = 'attendance.notification'
    _description = 'Attendance Notification'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    title = fields.Char(string="Title")
    message = fields.Text(string="Message")
    notification_type = fields.Selection([
        ('late', 'Late'),
        ('absence', 'Absence'),
        ('early_leave', 'Early Leave'),
        ('attendance_ok', 'Attendance OK')
    ], string='Notification Type', default='attendance_ok')
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now)
    is_read = fields.Boolean(string="Is Read", default=False)
    event_date = fields.Datetime(string="Event Date")
    check_in = fields.Datetime(string="Check-in")
    check_out = fields.Datetime(string="Check-out")
    department_id = fields.Many2one('hr.department', string="Department")
    company_id = fields.Many2one('res.company', string="Company")

    def mark_as_read(self):
        """Marks the notification as read."""
        self.is_read = True



