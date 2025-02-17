# -*- coding: utf-8 -*-

from odoo import models, fields, api


class dashboard(models.Model):
    _name = 'dashboard.dashboard'
    _description = 'dashboard.dashboard'

    class dashboard(models.Model):
        _name = 'dashboard.dashboard'
        _description = 'dashboard.dashboard'

    class EventManagementrequisicao(models.Model):
        """Event Management Dashboard"""
        _name = "costumer.event.management.dashboard"

        @api.model
        def get_event_management_dashboard(self):
            user = self.env.user

            total_material = self.env['stock.picking'].sudo().search_count(
                ['|', '|', ('create_uid', '=', user.id), ('responsavel_user', '=', user.id),
                 ('tecnico_user', '=', user.id)])
            total_maodeobra = self.env['requisicaomaodeobra.requisicaomaodeobra'].sudo().search_count(
                ['|', ('create_uid', '=', user.id), ('eng_responsavel', '=', user.id)])
            total_pagamento = self.env['requisicaopagamento.requisicaopagamento'].sudo().search_count(
                ['|', ('create_uid', '=', user.id), ('eng_responsavel', '=', user.id)])
            total_folha = self.env['folha.producao'].sudo().search_count(
                ['|', '|', ('create_uid', '=', user.id), ('eng_responsavel', '=', user.id),
                 ('tecnico_user', '=', user.id)])
            total_assistencia = self.env['ges.hr.daily.attendance'].sudo().search_count(
                ['|', ('create_uid', '=', user.id), ('eng_responsavel', '=', user.id)])
            data = {
                'total_material': total_material,
                'total_maodeobra': total_maodeobra,
                'total_pagamento': total_pagamento,
                'total_folha': total_folha,
                'total_assistencia': total_assistencia
            }
            return data