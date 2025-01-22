# -*- coding: utf-8 -*-

from odoo import models, fields, api


class portalinherit(models.Model):
    _name = 'portalinherit.portalinherit'
    _description = 'portalinherit.portalinherit'

    value = fields.Integer(string="valor2 ")
    value2 = fields.Float(string=" valor1")
    description = fields.Text()


class StockPickingTreeView(models.Model):
    _inherit = 'ir.ui.view'







