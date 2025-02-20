odoo.define('dashboardpontual.pontual_js', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session'); // Certifique-se de importar `session`

    const DashboardTemplate = AbstractAction.extend({
        template: 'pontualdashboard',

        start: function () {
            console.debug("[DEBUG] Iniciando o método start...");
            this._super.apply(this, arguments);

            setTimeout(() => {
                this.render_doughnut_chart();
                this.render_line_chart();
                this.render_bar_chart();
                // this.renderElement();
            }, 100);
        },

        render_doughnut_chart: function () {
            var self = this;

            if (typeof Chart === 'undefined') {
                console.error("Chart.js não foi carregado corretamente!");
                return;
            }

            var ctx = this.$('.myPieChart')[0]?.getContext('2d');

            if (!ctx) {
                console.error("Canvas não encontrado para o gráfico de doughnut!");
                return;
            }

            if (self.myPieChartInstance) {
                self.myPieChartInstance.destroy();
            }

            var totalPresents = $('#total_presents').text();
            var totalAbsents = $('#total_absents').text();
            var totalAtrasos = $('#total_atrasos').text();

            var data = {
                labels: ['Presentes', 'Ausentes', 'Atrasos'],
                datasets: [{
                    label: 'Assiduidade',
                    data: [parseInt(totalPresents) || 0, parseInt(totalAbsents) || 0, parseInt(totalAtrasos) || 0],
                    backgroundColor: [
                        '#71639e',
                        '#e74a3b',
                        '#36b9cc'
                    ],
                    hoverOffset: 4
                }]
            };

            self.myPieChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: data
            });
        },

        render_line_chart: function () {
            var self = this;

            if (typeof Chart === 'undefined') {
                console.error("Chart.js não foi carregado corretamente!");
                return;
            }

            var ctx = this.$('#myLineChart')[0]?.getContext('2d');

            if (!ctx) {
                console.error("Canvas não encontrado para o gráfico de linhas!");
                return;
            }

            if (self.myLineChartInstance) {
                self.myLineChartInstance.destroy();
            }

            const labels = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];

            const faltas_por_dia = self.faltas_por_dia || [0, 0, 0, 0, 0, 0, 0];

            const data = {
                labels: labels,
                datasets: [{
                    label: 'Faltas na Semana',
                    data: faltas_por_dia,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            };

            self.myLineChartInstance = new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        render_bar_chart: function () {
            var self = this;

            if (typeof Chart === 'undefined') {
                console.error("Chart.js não foi carregado corretamente!");
                return;
            }

            var ctx = this.$('#myBarChart')[0]?.getContext('2d');

            if (!ctx) {
                console.error("Canvas não encontrado para o gráfico de barras!");
                return;
            }

            if (self.myBarChartInstance) {
                self.myBarChartInstance.destroy();
            }

            const labels = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho'];
            const data = {
                labels: labels,
                datasets: [{
                    label: 'My First Dataset',
                    data: [65, 59, 80, 81, 56, 55, 40],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 159, 64, 0.2)',
                        'rgba(255, 205, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(201, 203, 207, 0.2)'
                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)',
                        'rgb(153, 102, 255)',
                        'rgb(201, 203, 207)'
                    ],
                    borderWidth: 1
                }]
            };

            self.myBarChartInstance = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        renderElement: function () {
            const self = this;
            this._super();

            setTimeout(() => {
                if (!session || !session.uid) {
                    console.error("Sessão não está disponível ou uid não está definido.");
                    return;
                }

                // Pega a empresa ativa da sessão
                const company_id = session.user_context.allowed_company_ids[0];
                if (!company_id) {
                    console.error("Nenhuma empresa ativa encontrada na sessão.");
                    return;
                }

                let today = new Date();
                let startOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 1)); // Segunda-feira
                let endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 7));   // Domingo

                rpc.query({
                    model: "pontual_js.pontual_js",
                    method: "get_pontual_js_data",
                    args: [startOfWeek.toISOString().slice(0, 10), endOfWeek.toISOString().slice(0, 10), company_id]
                }).then(function (result) {
                    let $total_presents = $('#total_presents');
                    let $total_absents = $('#total_absents');
                    let $total_atrasos = $('#total_atrasos');

                    if ($total_presents.length && $total_absents.length && $total_atrasos.length) {
                        $total_presents.empty().append(result['total_presents']);
                        $total_absents.empty().append(result['total_absents']);
                        $total_atrasos.empty().append(result['total_atrasos']);

                        self.faltas_por_dia = result['faltas_por_dia'];

                        self.render_doughnut_chart();
                        self.render_line_chart();
                        self.render_bar_chart();
                    } else {
                        console.warn("Os elementos do DOM ainda não estão disponíveis. Adiando renderização...");
                        setTimeout(() => self.renderElement(), 100);
                    }

                }).catch(function (error) {
                    console.error("Erro ao buscar os dados:", error);
                });
            }, 500);  // Pequeno delay para garantir que a DOM está pronta
        },
    });

    core.action_registry.add('dashboardpontual', DashboardTemplate);
    return DashboardTemplate;
});