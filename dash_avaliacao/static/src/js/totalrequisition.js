odoo.define('dash_avaliacao.EventManagement', function (require) {
    'use strict';
    const AbstractAction = require('web.AbstractAction');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const _t = core._t;

    const ActionMenu = AbstractAction.extend({
        template: 'eventManagements',
        events: {
            'click .total-nova': 'view_total_nova',
            'click .total-aprovar': 'view_total_aprovar',
            'click .total-espera': 'view_total_espera',
            'click .total-concluir': 'view_total_concluir',
            'click .total-cancelar': 'view_total_cancelar',
            'click .total-rejeitada': 'view_total_rejeitada',
            'click #departmentChart': 'onDepartmentChartClick',
            'click #comissaoChart': 'onComissaoChartClick',
            'click #monthlyChart': 'onMonthlyChartClick',
        },

        renderElement: function () {
            this._super();

            // Fetch data via RPC
            rpc.query({
                model: "costumer.management.dashboard",
                method: "get_management_dashboard",
            }).then(result => {
                $('#total_nova').empty().append(result['total_nova']);
                $('#total_aprovar').empty().append(result['total_aprovar']);
                $('#total_espera').empty().append(result['total_espera']);
                $('#total_concluir').empty().append(result['total_concluir']);
                $('#total_cancelar').empty().append(result['total_cancelar']);
                $('#total_rejeitar').empty().append(result['total_rejeitada']);

                const department_labels = result['department_data'].map(item => item.department);
                const department_counts = result['department_data'].map(item => item.count);

                const comissao_labels = result['comissao_data'].map(item => item.comissao);
                const comissao_counts = result['comissao_data'].map(item => item.count);

                const monthly_labels = result['monthly_data'].map(item => item.month);
                const monthly_counts = result['monthly_data'].map(item => item.count);

                const department_data = {
                    labels: department_labels,
                    datasets: [{
                        label: 'Registros por Departamento',
                        backgroundColor: 'rgba(255, 165, 0, 0.5)',
                        borderColor: 'rgba(255, 165, 0, 1)',
                        borderWidth: 1,
                        data: department_counts
                    }]
                };
                const comissao_data = {
                    labels: comissao_labels,
                    datasets: [{
                        label: 'Registros por Comissão',
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                        data: comissao_counts
                    }]
                };

                const monthly_data = {
                    labels: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
                    datasets: [{
                        label: 'Registros por Mês',
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        data: monthly_counts
                    }]
                };

                const ctx1 = document.getElementById('comissaoChart').getContext('2d');
                const ctx2 = document.getElementById('monthlyChart').getContext('2d');
                const ctx3 = document.getElementById('departmentChart').getContext('2d');

                new Chart(ctx2, {
                    type: 'line',
                    data: monthly_data,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Registros por Mês'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });

                new Chart(ctx1, {
                    type: 'doughnut',
                    data: comissao_data,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Registros por Comissão'
                            }
                        }
                    }
                });

                new Chart(ctx3, {
                    type: 'bar',
                    data: department_data,
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Registros por Departamento'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
        },

        onDepartmentChartClick: function (ev) {
            ev.preventDefault();
            const chartLabel = this.getChartLabel(ev, 'departmentChart');
            this.handleChartClick('departamento', chartLabel);
        },

        onComissaoChartClick: function (ev) {
            ev.preventDefault();
            const chartLabel = this.getChartLabel(ev, 'comissaoChart');
            this.handleChartClick('comissao_list', chartLabel);
        },

        onMonthlyChartClick: function (ev) {
            ev.preventDefault();
            const chartLabel = this.getChartLabel(ev, 'monthlyChart');
            this.handleChartClick('create_date', chartLabel);
        },

        getChartLabel: function (ev, chartId) {
            const canvas = ev.currentTarget;
            const chart = canvas.__chart__;
            if (!chart) {
                console.error('Instância do gráfico não encontrada.');
                return "Rótulo Não Encontrado";
            }

            const activePoint = chart.getElementsAtEventForMode(ev, 'nearest', { intersect: true }, true);
            if (activePoint.length) {
                const label = chart.data.labels[activePoint[0].index];
                return label ;

            }
            return "Nenhum Rótulo";
        },

        handleChartClick: function (field, chartLabel) {
            return this.do_action({
                name: _t('Detalhes de ' + chartLabel),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {
                    'company_id': this.getSession().company_id,
                    'default_company_id': this.getSession().company_id,
                },
                domain: [[field, '=', chartLabel]] // Use o campo apropriado e o valor do rótulo
            });
        },
        onDepartmentChartClick: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Fetch the current user ID
            var company_id = this.getSession().company_id;
            var chartLabel = this.getChartLabel(ev, 'departmentChart'); // Obtenha o rótulo do gráfico

            // Verifique se o rótulo foi encontrado antes de usá-lo
            if (!chartLabel) {
                console.error('Rótulo do departamento não encontrado.');
                return;
            }

             var domain = [
                ['create_uid', '=', user_id]
            ];

            return this.do_action({
                name: _t('Total Novos'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                },
                domain: domain
            });
        },

        view_total_nova: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Correctly fetch the current user ID
            var company_id = this.getSession().company_id;
            var domain = [
                ['status', '=', 'novo'],
                ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Novos'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [[false, 'list'],[false,'form']],
                target: 'current',
                 context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                 },
                domain: domain
            });
        },
        view_total_aprovar: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;
            var company_id = this.getSession().company_id;
            var domain = [
                 ['status', '=', 'aprovar'],
                 ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Aprovar'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [ [false, 'list'], [false, 'form']],
                target: 'current',
                context: {
                    'company_id': company_id,
                    'default_company_id': company_id,
                 },
                domain: domain
            });
        },

        view_total_espera: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Correctly fetch the current user ID
            var company_id = this.getSession().company_id;
            var domain = [
                 ['status', '=', 'espera'],
                 ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Avaliados'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [ [false, 'list'], [false, 'form'] ],
                target: 'current',
                context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                 },
                domain: domain
            });
        },

         view_total_concluir: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Correctly fetch the current user ID
            var company_id = this.getSession().company_id;
            var domain = [
                 ['status', '=', 'concluir'],
                 ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Concluidos'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [ [false, 'list'], [false, 'form'] ],
                target: 'current',
                context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                 },
                domain: domain
            });
        },
        view_total_cancelar: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Correctly fetch the current user ID
            var company_id = this.getSession().company_id;
            var domain = [
                 ['status', '=', 'cancelar'],
                 ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Cancelados'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [ [false, 'list'], [false, 'form'] ],
                target: 'current',
                context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                 },
                domain: domain
            });
        },


        view_total_rejeitada: function (ev) {
            ev.preventDefault();
            var user_id = this.getSession().uid;  // Correctly fetch the current user ID
            var company_id = this.getSession().company_id;
            var domain = [
                ['status', '=', 'rejeitar'],
                ['create_uid', '=', user_id]
            ];
            return this.do_action({
                name: _t('Total Rejeitados'),
                type: 'ir.actions.act_window',
                res_model: 'avaliar.funcionario',
                views: [ [false, 'list'], [false, 'form'] ],
                target: 'current',
                context: {
                    'company_id': company_id,  // Pass the current company ID in the context
                    'default_company_id': company_id,  // Set the default company ID for new records
                 },
                domain: domain
            });
        },

    });

    core.action_registry.add('event_dashboard', ActionMenu);
});



//                const data2 = {
//                    labels: ['Registros Novos', 'Registros Avaliados', 'Registros Aprovar', 'Registros Concluidos', 'Registros Cancelados', 'Registros Rejeitados'],
//                    datasets: [{
//                        label: 'Quantidade',
//                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
//                        borderColor: 'rgba(255, 99, 132, 1)',
//                        borderWidth: 1,
//                        data: [
//                            result['total_material'],
//                            result['total_pagamento'],
//                            result['total_maodeobra'],
//                            result['total_folha'],
//                            result['total_assistencia'],
//                            result['total_rejeitada']
//                        ]
//                    }]
//                };
