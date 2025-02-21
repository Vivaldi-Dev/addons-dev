// odoo.define('dashboardpontual.pontual_js', function (require) {
//     "use strict";
//
//     var AbstractAction = require('web.AbstractAction');
//     var core = require('web.core');
//     var rpc = require('web.rpc');
//     var session = require('web.session');
//
//     const DashboardTemplate = AbstractAction.extend({
//         template: 'pontualdashboard',
//
//         start: function () {
//             this._super.apply(this, arguments);
//
//             $('#datePickerPanel').hide();
//
//             this.$el.on('click', '#toggleCalendarButton', function () {
//                 $('#datePickerPanel').toggle();
//                 console.log('Painel de datas alternado');
//             });
//
//             this.$el.on('click', '#applyButton', function () {
//                 const startDate = $('#startDate').val();
//                 const endDate = $('#endDate').val();
//
//                 if (!startDate || !endDate) {
//                     console.error("Por favor, selecione ambas as datas.");
//                     return;
//                 }
//
//                 self.renderElement(startDate, endDate);
//             });
//
//             const self = this;
//
//             setTimeout(() => {
//                 self.renderElement();
//             }, 100);
//         },
//
//         render_doughnut_chart: function () {
//             var self = this;
//
//             if (typeof Chart === 'undefined') {
//                 console.error("Chart.js não foi carregado corretamente!");
//                 return;
//             }
//
//             var ctx = this.$('.myPieChart')[0]?.getContext('2d');
//
//             if (!ctx) {
//                 console.error("Canvas não encontrado para o gráfico de doughnut!");
//                 return;
//             }
//
//             if (self.myPieChartInstance) {
//                 self.myPieChartInstance.destroy();
//             }
//
//             var totalPresents = $('#total_presents').text();
//             var totalAbsents = $('#total_absents').text();
//             var totalAtrasos = $('#total_atrasos').text();
//
//             var data = {
//                 labels: ['Presentes', 'Ausentes', 'Atrasos'],
//                 datasets: [{
//                     label: 'Assiduidade',
//                     data: [parseInt(totalPresents) || 0, parseInt(totalAbsents) || 0, parseInt(totalAtrasos) || 0],
//                     backgroundColor: [
//                         '#71639e',
//                         '#e74a3b',
//                         '#36b9cc'
//                     ],
//                     hoverOffset: 4
//                 }]
//             };
//
//             self.myPieChartInstance = new Chart(ctx, {
//                 type: 'doughnut',
//                 data: data
//             });
//         },
//
//         render_line_chart: function () {
//             var self = this;
//
//             if (typeof Chart === 'undefined') {
//                 console.error("Chart.js não foi carregado corretamente!");
//                 return;
//             }
//
//             var ctx = this.$('#myLineChart')[0]?.getContext('2d');
//
//             if (!ctx) {
//                 console.error("Canvas não encontrado para o gráfico de linhas!");
//                 return;
//             }
//
//             if (self.myLineChartInstance) {
//                 self.myLineChartInstance.destroy();
//             }
//
//             const attendance_by_day = self.attendance_by_day || [];
//             const labels = attendance_by_day.map(day => day.day_of_week);
//             const ausentes_data = attendance_by_day.map(day => day.ausentes);
//             const presentes_data = attendance_by_day.map(day => day.presentes);
//
//             console.log("Labels:", labels);
//             console.log("Dados de ausentes:", ausentes_data);
//             console.log("Dados de presentes:", presentes_data);
//
//             const data = {
//                 labels: labels,
//                 datasets: [
//                     {
//                         label: 'Faltas na Semana',
//                         data: ausentes_data,
//                         fill: false,
//                         borderColor: 'rgb(255, 99, 132)',
//                         tension: 0.1
//                     },
//                     {
//                         label: 'Presentes na Semana',
//                         data: presentes_data,
//                         fill: false,
//                         borderColor: '#71639e',
//                         tension: 0.1
//                     }
//                 ]
//             };
//
//             self.myLineChartInstance = new Chart(ctx, {
//                 type: 'line',
//                 data: data,
//                 options: {
//                     responsive: true,
//                     maintainAspectRatio: false,
//                     scales: {
//                         y: {
//                             beginAtZero: true
//                         }
//                     }
//                 }
//             });
//         },
//
//         render_bar_chart: function () {
//             var self = this;
//
//             if (typeof Chart === 'undefined') {
//                 console.error("Chart.js não foi carregado corretamente!");
//                 return;
//             }
//
//             var ctx = this.$('#myBarChart')[0]?.getContext('2d');
//
//             if (!ctx) {
//                 console.error("Canvas não encontrado para o gráfico de barras!");
//                 return;
//             }
//
//             if (self.myBarChartInstance) {
//                 self.myBarChartInstance.destroy();
//             }
//
//             if (!self.attendance_by_day || self.attendance_by_day.length === 0) {
//                 console.warn("Nenhum dado de presença disponível para exibição no gráfico de barras.");
//                 return;
//             }
//
//             const labels = self.attendance_by_day.map(item => item.date);
//
//             const presentesData = self.attendance_by_day.map(item => item.presentes);
//             const ausentesData = self.attendance_by_day.map(item => item.ausentes);
//
//             const data = {
//                 labels: labels,
//                 datasets: [
//                     {
//                         label: 'Presentes',
//                         data: presentesData,
//                         backgroundColor: 'rgba(75, 192, 192, 0.6)',
//                         borderColor: 'rgba(75, 192, 192, 1)',
//                         borderWidth: 1
//                     },
//                     {
//                         label: 'Ausentes',
//                         data: ausentesData,
//                         backgroundColor: 'rgba(255, 99, 132, 0.6)',
//                         borderColor: 'rgba(255, 99, 132, 1)',
//                         borderWidth: 1
//                     }
//                 ]
//             };
//
//             self.myBarChartInstance = new Chart(ctx, {
//                 type: 'bar',
//                 data: data,
//                 options: {
//                     responsive: true,
//                     maintainAspectRatio: false,
//                     scales: {
//                         y: {
//                             beginAtZero: true
//                         }
//                     }
//                 }
//             });
//         },
//
//         renderElement: function (customStartDate, customEndDate) {
//             const self = this;
//             this._super();
//
//             setTimeout(() => {
//                 if (!session || !session.uid) {
//                     console.error("Sessão não está disponível ou uid não está definido.");
//                     return;
//                 }
//
//                 const company_id = session.user_context.allowed_company_ids[0];
//                 if (!company_id) {
//                     console.error("Nenhuma empresa ativa encontrada na sessão.");
//                     return;
//                 }
//
//                 let startDate, endDate;
//
//                 if (customStartDate && customEndDate) {
//
//                     startDate = customStartDate;
//                     endDate = customEndDate;
//                 } else {
//
//                     let today = new Date();
//                     startDate =  new Date(today.setDate(today.getDate() - today.getDay() + 1));
//                     endDate = new new Date(today.setDate(today.getDate() - today.getDay() + 7));
//                     startDate = startDate.toISOString().slice(0, 10);
//                     endDate = endDate.toISOString().slice(0, 10);
//                 }
//
//
//                 rpc.query({
//                     model: "pontual_js.pontual_js",
//                     method: "get_pontual_js_data",
//                     args: [startDate, endDate, company_id]
//                 }).then(function (result) {
//                     let totalFuncionarios = result['total_employees'];
//                     let totalPresents = result['total_presents'];
//                     let totalAbsents = result['total_absents'];
//                     let totalAtrasos = result['total_atrasos'];
//
//                     let presentes = result['total_presents'];
//                     let ausentes = result['total_absents'];
//                     let funcionario = result['total_employees'];
//                     let atrsos = result['total_atrasos'];
//
//                     let percentPresents = (presentes / funcionario) * 100;
//                     let percentAbsents = (ausentes / funcionario) * 100;
//                     let percentAtrasos = (atrsos / funcionario) * 100;
//
//                     let pPresents = ((presentes / funcionario) * 100).toFixed(2);
//                     let pAbsents = ((ausentes / funcionario) * 100).toFixed(2);
//                     let ptAtrasos = ((atrsos / funcionario) * 100).toFixed(2);
//
//                     $('#total_presents').text(totalPresents);
//                     $('#total_absents').text(totalAbsents);
//                     $('#total_atrasos').text(totalAtrasos);
//
//                     $('.custom-prents').css('width', pPresents + '%').attr('aria-valuenow', pPresents);
//                     $('.bg-danger').css('width', pAbsents + '%').attr('aria-valuenow', pAbsents);
//                     $('.custom-atrsos').css('width', ptAtrasos + '%').attr('aria-valuenow', ptAtrasos);
//
//                     $('.text-success-custom').html(`<i class="fas fa-user-check"></i> ${pPresents}%`);
//                     $('.text-danger-custom').html(`<i class="fas fa-user-times"></i> ${pAbsents}%`);
//                     $('.text-warning-custom').html(`<i class="fas fa-clock"></i> ${ptAtrasos}%`);
//
//                     $('.text-success-custom').closest('div').find('small').text(`Presentes (${totalPresents} funcionários)`);
//                     $('.text-danger-custom').closest('div').find('small').text(`Ausentes (${totalAbsents} funcionários)`);
//                     $('.text-warning-custom').closest('div').find('small').text(`Atrasos (${totalAtrasos} funcionários)`);
//
//                     $('.custom-prents').closest('.progress').prev().find('.float-right').text(percentPresents.toFixed(2) + '%');
//                     $('.bg-danger').closest('.progress').prev().find('.float-right').text(percentAbsents.toFixed(2) + '%');
//                     $('.custom-atrsos').closest('.progress').prev().find('.float-right').text(percentAtrasos.toFixed(2) + '%');
//
//                     self.attendance_by_day = result['attendance_by_day'];
//                     self.render_doughnut_chart();
//                     self.render_line_chart();
//                     self.render_bar_chart();
//                 }).catch(function (error) {
//                     console.error("Erro ao buscar os dados:", error);
//                 });
//             }, 500);
//         },
//
//     });
//
//     core.action_registry.add('dashboardpontual', DashboardTemplate);
//     return DashboardTemplate;
// });