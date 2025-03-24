# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class js_pontual_candidate(models.Model):
#     _name = 'js_pontual_candidate.js_pontual_candidate'
#     _description = 'js_pontual_candidate.js_pontual_candidate'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
