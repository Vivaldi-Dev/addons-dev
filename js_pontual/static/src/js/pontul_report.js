odoo.define('pontual.js_pontual', function (require) {
    "use strict"

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    const reporttemplate = AbstractAction.extend({

        template: 'reportpontual',

        start: function () {
            this._super.apply(this, arguments);
            this.render_doughnut_chart();
            this.render_bar_line_chart();
            this.renderElement();
        },


        render_doughnut_chart: function () {
            var self = this;

            if (typeof Chart === 'undefined') {
                console.error("Chart.js não foi carregado corretamente!");
                return;
            }

            var ctx = this.$('.project_hours')[0]?.getContext('2d');

            if (!ctx) {
                console.error("Canvas não encontrado!");
                return;
            }

            var data = {
                labels: ['Red', 'Blue', 'Yellow'],
                datasets: [{
                    label: 'My First Dataset',
                    data: [300, 50, 100],
                    backgroundColor: [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)',
                        'rgb(255, 205, 86)'
                    ],
                    hoverOffset: 4
                }]
            };

            new Chart(ctx, {
                type: 'doughnut',
                data: data
            });
        },

        render_bar_line_chart: function () {
            var self = this;

            if (typeof Chart === 'undefined') {
                console.error("Chart.js não foi carregado corretamente!");
                return;
            }

            var ctx2 = this.$('.line_chart')[0]?.getContext('2d');

            if (!ctx2) {
                console.error("Canvas para gráfico de linha não encontrado!");
                return;
            }

            new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: ['January', 'February', 'March', 'April'],
                    datasets: [
                        {
                            type: 'bar',
                            label: 'Bar Dataset',
                            data: [10, 20, 30, 40],
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)'
                        },
                        {
                            type: 'line',
                            label: 'Line Dataset',
                            data: [50, 50, 50, 50],
                            fill: false,
                            borderColor: 'rgb(54, 162, 235)'
                        }
                    ]
                }
            });
        },

        renderElement: function () {
            const self = this;
            this._super();

            let today = new Date().toISOString().slice(0, 10);
            const session = this.getSession();

            rpc.query({
                model: "res.users",
                method: "read",
                args: [[session.uid], ["company_id"]]
            }).then(function (user_data) {
                if (user_data && user_data.length > 0) {
                    let company_id = user_data[0].company_id[0];

                    rpc.query({
                        model: "js_pontual.js_pontual",
                        method: "get_data_for_js_pontual",
                        args: [today, today, company_id]
                    }).then(function (result) {
                        $('#total_presents').empty().append(result['total_presents']);
                        $('#total_absents').empty().append(result['total_absents']);

                        // **Recria os gráficos depois de atualizar os elementos**
                        self.render_doughnut_chart();
                        self.render_bar_line_chart();

                    }).catch(function (error) {
                        console.error("Erro ao buscar os dados:", error);
                    });
                } else {
                    console.error("Erro: Nenhum dado de usuário encontrado.");
                }
            }).catch(function (error) {
                console.error("Erro ao buscar company_id:", error);
            });
        }


    });

    core.action_registry.add('pontual', reporttemplate);
    return reporttemplate;
});