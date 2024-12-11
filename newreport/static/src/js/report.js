odoo.define('sdsdsd.reportss', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    const TableDashboard = AbstractAction.extend({
        template: 'Tablerender',

        start: function () {
            this._super.apply(this, arguments);
            this._fetchData();
            this._setupEventListeners();
        },

        _fetchData: function () {
            const self = this;
            console.log("Iniciando a requisição para a API...");

            fetch('/newreport/newreport', {
                method: 'GET',
                headers: {}
            })
                .then(response => {
                    console.log("response:", response);
                    if (!response.ok) {
                        throw new Error('Network response was not ok: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Data:", data);
                    self._updateTable(data);
                })
                .catch(error => {
                    console.error('Houve um problema com a requisição Fetch:', error);
                });
        },

        _updateTable: function (data) {

            const tableBodies = ['#tableBody1', '#tableBody2', '#tableBody3'];
            tableBodies.forEach(id => {
                this.$el.find(id).empty();
            });


            data.forEach(item => {
                const currentBalanceFormatted = this._formatCurrency(item.current_balance);
                const prefixoIndex = {
                    "3.1.1": 1,
                    "3.1.2": 2,
                    "3.1.3": 3
                };

                const prefixo = item.code.split('.').slice(0, 3).join('.');
                const index = prefixoIndex[prefixo];

                if (index) {
                    const row = `<tr>
                        <td>${item.name}</td>
                        <td>${item.code}</td>
                        <td>${currentBalanceFormatted}</td>
                        <td>2024</td>
                    </tr>`;
                    this.$el.find(`#tableBody${index}`).append(row);
                }
            });
        },

        _formatCurrency: function (amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
            }).format(amount);
        },


        _setupEventListeners: function () {
            const self = this;

            const toggleButton = this.$el.find('#toggleDateRange')[0];
            if (toggleButton) {
                toggleButton.addEventListener('click', function () {
                    const dateRangeDiv = self.$el.find('#dateRangeInputs')[0];
                    dateRangeDiv.style.display = (dateRangeDiv.style.display === "none" || dateRangeDiv.style.display === "") ? "block" : "none";
                });
            } else {
                console.error("Botão 'toggleDateRange' não encontrado.");
            }

            const applyButton = this.$el.find('.btn.btn-primary')[0];
            if (applyButton) {
                applyButton.addEventListener('click', function () {
                    const startDate = self.$el.find('#startDate').val();
                    const endDate = self.$el.find('#endDate').val();

                    if (startDate && endDate) {
                        self._updateTableHeaders(startDate, endDate);
                    } else {
                        alert('Por favor, preencha ambas as datas.');
                    }
                });
            } else {
                console.error("Botão 'Aplicar' não encontrado.");
            }
        },

        _updateTableHeaders: function (startDate, endDate) {
            const startFormatted = new Date(startDate).toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit'
            });
            const endFormatted = new Date(endDate).toLocaleDateString('pt-BR', {day: '2-digit', month: '2-digit'});

            const thStartDate = this.$el.find('th:nth-child(2)')[0];
            const thEndDate = this.$el.find('th:nth-child(3)')[0];

            if (thStartDate) {
                thStartDate.textContent = startFormatted;
            }
            if (thEndDate) {
                thEndDate.textContent = endFormatted;
            }
        }
    });

    core.action_registry.add('reportss', TableDashboard);

    return TableDashboard;
});
