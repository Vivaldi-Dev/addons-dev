odoo.define('dashPontual.Dashboard', function (require) {
    "use strict"

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;

    let myPieChart;
    let myLineChart;

    const dashpontualTemplate = AbstractAction.extend({
        template: 'dashpontual',

        events: {
            'click .total-presente': 'view_presentes',
            'click .total-ausentes': 'view_ausentes',
            'click .total-atrasos': 'view_atraos',
            'click #toggleCalendarButton': 'toggleCalendar',
        },


        start: function () {
            this._super.apply(this, arguments);


            this.$el.on('click', '#toggleCalendarButton', function () {
                $('#datePickerPanel').toggleClass('show');

            });

            let {startOfWeek, endOfWeek} = this.getCurrentWeek();
            $('#startDate').val(startOfWeek);
            $('#endDate').val(endOfWeek);

            this.getPontualData(startOfWeek, endOfWeek, true);

            this.$el.on('click', '.toggle-calendar-button', this.toggleCalendar.bind(this));


            this.$el.on('click', '#applyButton', () => {
                let startDate = $('#startDate').val();
                let endDate = $('#endDate').val();
             
                this.getPontualData(startDate, endDate);
            });
        },

        toggleCalendar: function (ev) {
            ev.preventDefault();

            $('.date-picker-panel').toggleClass('show');
        },

        view_presentes: function (ev) {
            ev.preventDefault();

            let startDate = $('#startDate').val();
            let endDate = $('#endDate').val();

            let currentDate = moment().format("YYYY-MM-DD");
            startDate = startDate || currentDate;
            endDate = endDate || currentDate;



            return this.do_action({
                name: _t('Attendances'),
                type: 'ir.actions.act_window',
                res_model: 'hr.attendance',
                views: [[false, 'list'], [false, 'kanban'], [false, 'form'], [false, 'activity']],
                target: 'current',
                domain: [
                    ['check_in', '>=', startDate + ' 00:00:00'],
                    ['check_in', '<=', endDate + ' 23:59:59'],

                ],

            });
        },

        view_ausentes: function (ev) {
            ev.preventDefault();

            let startDate = $('#startDate').val();
            let endDate = $('#endDate').val();

            let currentDate = moment().format("YYYY-MM-DD");
            startDate = startDate || currentDate;
            endDate = endDate || currentDate;



            return this.do_action({
                name: _t('Attendances'),
                type: 'ir.actions.act_window',
                res_model: 'hr.employees.without.checkin',
                views: [[false, 'list'], [false, 'kanban'], [false, 'form'], [false, 'activity']],
                target: 'current',
                domain: [
                    ['date', '>=', startDate],
                    ['date', '<=', endDate]
                ],
                context: {
                    'start_date': startDate,
                    'end_date': endDate
                }
            });
        },

        view_atraos: function (ev) {
            ev.preventDefault();

            let startDate = $('#startDate').val();
            let endDate = $('#endDate').val();

            let currentDate = moment().format("YYYY-MM-DD");
            startDate = startDate || currentDate;
            endDate = endDate || currentDate;



            return this.do_action({
                name: _t('Attendances'),
                type: 'ir.actions.act_window',
                res_model: 'hr.attendance',
                views: [[false, 'list'], [false, 'kanban'], [false, 'form'], [false, 'activity']],
                target: 'current',
                domain: [
                    ['delay_minutes', '>', 0],
                    ['check_in', '>=', startDate + ' 00:00:00'],
                    ['check_in', '<=', endDate + ' 23:59:59']
                ],

            });
        },


        getPontualData: function (startDate, endDate, isInitialLoad = false) {
            if (!session || !session.uid) {

                return;
            }

            const company_id = session.user_context.allowed_company_ids[0];
            if (!company_id) {

                return;
            }

            let currentDate = this.getCurrentDate();
            let doughnutStartDate = isInitialLoad ? currentDate : (startDate || currentDate);
            let doughnutEndDate = isInitialLoad ? currentDate : (endDate || currentDate);

            let {startOfWeek, endOfWeek} = this.getCurrentWeek();
            let lineChartStartDate = isInitialLoad ? startOfWeek : (startDate || startOfWeek);
            let lineChartEndDate = isInitialLoad ? endOfWeek : (endDate || endOfWeek);

            let {firstDayOfMonth, lastDayOfMonth} = this.getCurrentMonth();
            let barChartStartDate = isInitialLoad ? firstDayOfMonth : (startDate || firstDayOfMonth);
            let barChartEndDate = isInitialLoad ? lastDayOfMonth : (endDate || lastDayOfMonth);

            rpc.query({
                model: 'dashboard_pontual.dashboard_pontual',
                method: 'get_pontual_js_data',
                args: [doughnutStartDate, doughnutEndDate, company_id]
            }).then((data) => {
                $('#total_presents').text(data.total_presents);
                $('#total_absents').text(data.total_absents);
                $('#total_atrasos').text(data.total_atrasos);

                this.render_doughnut_chart(data.total_presents, data.total_absents, data.total_atrasos);
                this.updateProgressBars(data.total_presents, data.total_absents, data.total_atrasos);
            }).catch((error) => {

            });

            rpc.query({
                model: 'dashboard_pontual.dashboard_pontual',
                method: 'get_pontual_js_data',
                args: [lineChartStartDate, lineChartEndDate, company_id]
            }).then((data) => {
                this.render_line_chart(data.attendance_by_day);
            }).catch((error) => {

            });

            rpc.query({
                model: 'dashboard_pontual.dashboard_pontual',
                method: 'get_pontual_js_data',
                args: [barChartStartDate, barChartEndDate, company_id]
            }).then((data) => {
                this.render_bar_chart(data.attendance_by_day);
            }).catch((error) => {

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

            $('.text-success-custom').html(`<i class="fas fa-user-check"></i> ${presentsPercentage.toFixed(0)}%`);
            $('.text-danger-custom').html(`<i class="fas fa-user-times"></i> ${absentsPercentage.toFixed(0)}%`);
            $('.text-warning-custom').html(`<i class="fas fa-clock"></i> ${atrasosPercentage.toFixed(0)}%`);
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

        getCurrentDate: function () {
            let today = new Date();
            return today.toISOString().split('T')[0];
        },

        getCurrentWeek: function () {
            let today = new Date();
            let first = today.getDate() - today.getDay();
            let last = first + 6;

            let startOfWeek = new Date(today.setDate(first)).toISOString().split('T')[0];
            let endOfWeek = new Date(today.setDate(last)).toISOString().split('T')[0];

            return {startOfWeek, endOfWeek};
        },

        getCurrentMonth: function () {
            let today = new Date();
            let firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
            let lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

            return {firstDayOfMonth, lastDayOfMonth};
        },


        render_bar_chart: function (attendance_by_day) {
            let ctx = document.getElementById("myBarChart").getContext("2d");

            let labels = attendance_by_day.map(day => day.date);
            let presentes = attendance_by_day.map(day => day.presentes);
            let ausentes = attendance_by_day.map(day => day.ausentes);

            if (this.myBarChart) {
                this.myBarChart.destroy();
            }

            this.myBarChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: "Presentes",
                            data: presentes,
                            backgroundColor: "#4CAF50",
                            borderWidth: 1
                        },
                        {
                            label: "Ausentes",
                            data: ausentes,
                            backgroundColor: "#F44336",
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        zoom: {
                            zoom: {
                                wheel: {
                                    enabled: true,
                                },
                                pinch: {
                                    enabled: true
                                },
                                mode: 'x'
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: "Dias do Mês"
                            },
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45
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


            this.myBarChart.zoom(1.5);
        }


    });

    core.action_registry.add('dashPontual', dashpontualTemplate);
    return dashpontualTemplate;
});
