# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
# import requests
# import base64
# from datetime import datetime
# from datetime import datetime
# import base64
from collections import defaultdict




class dashAvaliacao(models.Model):
    _name = 'dash.avaliacao'
    _description = 'Dasboard Avaliacao'

class EventManagement(models.Model):
    """Event Management Dashboard"""
    _name = "costumer.management.dashboard"
    _description = __doc__

    @api.model
    def get_management_dashboard(self):
        user = self.env.user
        total_nova = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'novo'),('create_uid', '=', user.id)])
        total_aprovar = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'aprovar'),('create_uid', '=', user.id)])
        total_espera = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'espera'),('create_uid', '=', user.id)])
        total_concluir = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'concluir'),('create_uid', '=', user.id)])
        total_cancelar = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'cancelar'),('create_uid', '=', user.id)])
        total_rejeitada = self.env['avaliar.funcionario'].sudo().search_count([('status', '=', 'rejeitar'),('create_uid', '=', user.id)])
        departments = self.env['hr.department'].sudo().search([])
        department_data = []
        for department in departments:
            count = self.env['avaliar.funcionario'].sudo().search_count([('departamento', '=', department.id),('create_uid', '=', user.id)])
            department_data.append({
                'department': department.name,
                'count': count
            })
            # print(f"Department: {department.name}, Count: {count}")
        comissoes = self.env['comissao.template'].sudo().search([])
        comissao_data = []
        for comissao in comissoes:
            count = self.env['avaliar.funcionario'].sudo().search_count([('comissao_list', '=', comissao.id)])
            if count > 0:
                comissao_data.append({
                    'comissao': comissao.name,
                    'count': count
                })

        self.env.cr.execute("""
                    SELECT
                        TO_CHAR(create_date, 'YYYY-MM') AS month,
                        COUNT(*) AS count
                    FROM
                        avaliar_funcionario
                    GROUP BY
                        TO_CHAR(create_date, 'YYYY-MM')
                    ORDER BY
                        TO_CHAR(create_date, 'YYYY-MM')
                """)
        monthly_data = self.env.cr.fetchall()

        monthly_counts = defaultdict(int, {m: c for m, c in monthly_data})

        months = ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09',
                  '2024-10', '2024-11', '2024-12']
        monthly_data_complete = [{'month': month, 'count': monthly_counts[month]} for month in months]

        monthly_data = self.env.cr.fetchall()
        data = {
            'total_nova': total_nova,
            'total_aprovar': total_aprovar,
            'total_espera': total_espera,
            'total_concluir': total_concluir,
            'total_cancelar': total_cancelar,
            'total_rejeitada': total_rejeitada,
            'department_data': department_data,
            'comissao_data': comissao_data,
            'monthly_data': monthly_data_complete

        }
        return data
