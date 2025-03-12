odoo.define('dashPontual.dashboard_pontual', function (require) {
    "use strict"

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');

    let myPieChart;
    let myLineChart;

    const dashpontualTemplate = AbstractAction.extend({
        template: 'dashpontual',

        start: function () {
            this._super.apply(this, arguments);

            let {startOfWeek, endOfWeek} = this.getCurrentWeek();
            $('#startDate').val(startOfWeek);
            $('#endDate').val(endOfWeek);

            this.getPontualData(startOfWeek, endOfWeek, true);

            this.$el.on('click', '#toggleCalendarButton', function () {
                $('#datePickerPanel').toggleClass('show');
            });

            this.$el.on('click', '#applyButton', () => {
                let startDate = $('#startDate').val();
                let endDate = $('#endDate').val();
                this.getPontualData(startDate, endDate);
            });
        },

        getPontualData: function (startDate, endDate, isInitialLoad = false) {
            if (!session || !session.uid) {
                console.error("Sessão não está disponível ou uid não está definido.");
                return;
            }

            const company_id = session.user_context.allowed_company_ids[0];
            if (!company_id) {
                console.error("Nenhuma empresa ativa encontrada na sessão.");
                return;
            }

            let today = new Date().toISOString().split('T')[0];

            let requestStartDate = isInitialLoad ? today : startDate;
            let requestEndDate = isInitialLoad ? today : endDate;

            rpc.query({
                model: 'dashboard_pontual.dashboard_pontual',
                method: 'get_pontual_js_data',
                args: [requestStartDate, requestEndDate, company_id]
            }).then((data) => {
                $('#total_presents').text(data.total_presents);
                $('#total_absents').text(data.total_absents);
                $('#total_atrasos').text(data.total_atrasos);

                this.render_doughnut_chart(data.total_presents, data.total_absents, data.total_atrasos);

                // Atualizar barras de progresso
                this.updateProgressBars(data.total_presents, data.total_absents, data.total_atrasos);
            }).catch(function (error) {
                console.error("Erro ao buscar dados: ", error);
            });

            let lineChartStartDate = isInitialLoad ? this.getCurrentWeek().startOfWeek : startDate;
            let lineChartEndDate = isInitialLoad ? this.getCurrentWeek().endOfWeek : endDate;

            rpc.query({
                model: 'dashboard_pontual.dashboard_pontual',
                method: 'get_pontual_js_data',
                args: [lineChartStartDate, lineChartEndDate, company_id]
            }).then((data) => {
                this.render_line_chart(data.attendance_by_day);
            }).catch(function (error) {
                console.error("Erro ao buscar dados para o gráfico de linha: ", error);
            });
        },


        updateProgressBars: function (presents, absents, atrasos) {
            let total = presents + absents + atrasos;
            let presentsPercentage = total > 0 ? (presents / total) * 100 : 0;
            let absentsPercentage = total > 0 ? (absents / total) * 100 : 0;
            let atrasosPercentage = total > 0 ? (atrasos / total) * 100 : 0;


            $('#presents-percentage').text(presentsPercentage.toFixed(0) + "%");
            $('#absents-percentage').text(absentsPercentage.toFixed(0) + "%");
            $('#atrasos-percentage').text(atrasosPercentage.toFixed(0) + "%");


            $('.custom-prents').css('width', presentsPercentage + "%").attr('aria-valuenow', presentsPercentage);
            $('.progress-bar.bg-danger').css('width', absentsPercentage + "%").attr('aria-valuenow', absentsPercentage);
            $('.custom-atrsos').css('width', atrasosPercentage + "%").attr('aria-valuenow', atrasosPercentage);


            $('#presents-text').html(`<i class="fas fa-user-check"></i> ${presentsPercentage.toFixed(0)}%`);
            $('#presents-count').text(`Presentes (${presents} funcionários)`);

            $('#absents-text').html(`<i class="fas fa-user-times"></i> ${absentsPercentage.toFixed(0)}%`);
            $('#absents-count').text(`Ausentes (${absents} funcionários)`);

            $('#atrasos-text').html(`<i class="fas fa-clock"></i> ${atrasosPercentage.toFixed(0)}%`);
            $('#atrasos-count').text(`Atrasos (${atrasos} funcionários)`);
        },



        render_doughnut_chart: function (presentes, ausentes, atrasos) {
            let ctx = document.getElementById("myPieChart").getContext("2d");

            if (myPieChart) {
                myPieChart.destroy();
            }

            myPieChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ["Presentes", "Ausentes", "Atrasos"],
                    datasets: [{
                        data: [presentes, ausentes, atrasos],
                        backgroundColor: ["#4CAF50", "#F44336", "#FF9800"],
                        hoverBackgroundColor: ["#45A049", "#D32F2F", "#FB8C00"],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        render_line_chart: function (attendance_by_day) {
            let ctx = document.getElementById("myLineChart").getContext("2d");

            let labels = attendance_by_day.map(day => day.day_of_week);
            let presentes = attendance_by_day.map(day => day.presentes);
            let ausentes = attendance_by_day.map(day => day.ausentes);


            if (myLineChart) {
                myLineChart.destroy();
            }

            myLineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: "Presentes",
                            data: presentes,
                            borderColor: "#4CAF50",
                            backgroundColor: "rgba(76, 175, 80, 0.2)",
                            borderWidth: 2,
                            fill: true
                        },
                        {
                            label: "Ausentes",
                            data: ausentes,
                            borderColor: "#F44336",
                            backgroundColor: "rgba(244, 67, 54, 0.2)",
                            borderWidth: 2,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: "Dias da Semana"
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: "Quantidade de Funcionários"
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        getCurrentWeek: function () {
            let today = new Date();
            let first = today.getDate() - today.getDay();
            let last = first + 6;

            let startOfWeek = new Date(today.setDate(first)).toISOString().split('T')[0];
            let endOfWeek = new Date(today.setDate(last)).toISOString().split('T')[0];

            return {startOfWeek, endOfWeek};
        }
    });

    core.action_registry.add('dashPontual', dashpontualTemplate);
    return dashpontualTemplate;
});