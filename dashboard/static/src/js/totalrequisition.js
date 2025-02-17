odoo.define('dashboard.eventManagementrequisicoes', function (require) {
    'use strict';
    const AbstractAction = require('web.AbstractAction');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const _t = core._t;

    const ActionMenu = AbstractAction.extend({
        template: 'eventManagementrequisicoes',
        events: {
            'click .total-material': 'view_total_material',
            'click .total-mao-obra': 'view_total_mao_obra',
            'click .total-pagamento': 'view_total_pagamento',
        },

        renderElement: function () {
            const self = this;
            this._super();
            rpc.query({
                model: "event.management.requisicoes",
                method: "get_event_management_requisicoes",
            }).then(function (result) {
                $('#total_material').empty().append(result['total_material']);
                $('#total_maodeobra').empty().append(result['total_maodeobra']);
                $('#total_pagamento').empty().append(result['total_pagamento']);
            });
        },

        view_total_material: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('Total Material'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form'], [false, 'calendar'], [false, 'activity']],
                target: 'current'
            });
        },

        view_total_mao_obra: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('Total Mao-de-obra'),
                type: 'ir.actions.act_window',
                res_model: 'requisicaomaodeobra.requisicaomaodeobra',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form'],  [false, 'activity']],
                target: 'current'
            });
        },

        view_total_pagamento: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('Total Pagamento'),
                type: 'ir.actions.act_window',
                res_model: 'requisicaopagamento.requisicaopagamento',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form'],  [false, 'activity']],
                target: 'current'
            });
        },
    });

    core.action_registry.add('event_requisicao_dashboard', ActionMenu);
});