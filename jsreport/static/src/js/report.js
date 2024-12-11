odoo.define('reportar.jsreport', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    function loadHtml2Pdf() {
        return new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
            script.onload = () => resolve(script);
            document.head.appendChild(script);
        })
    }

    const Tablereport = AbstractAction.extend({
        template: 'Reportable',

        start: function () {
            this._super.apply(this, arguments);
            loadHtml2Pdf().then(() => {
                this._initializeSelect2();
                this._fetchReports();
                this._setupEventListeners();
                this._fetchOdooUsers();
            });

        },

        _initializeSelect2: function () {
            this.$('#revenueTypes').select2({
                placeholder: 'Selecione um relatório',
                allowClear: true,
            });
        },

        _fetchReports: function () {
            console.log("Buscando relatórios disponíveis...");
            fetch('/report/subcontas', {
                method: 'GET',
                headers: {}
            })
                .then(this._handleFetchResponse)
                .then(data => {
                    console.log("Relatórios recebidos:", data);
                    if (Array.isArray(data)) {
                        this.populateReportTypes(data);
                        this.appendTotal(data);
                    } else {
                        console.error('Esperado um array de relatórios, mas recebeu:', data);
                    }
                })
                .catch(error => {
                    console.error('Erro ao buscar relatórios:', error);
                });
        },

        _fetchOdooUsers: function () {
            fetch('/report/odoo_users', {
                method: 'GET',
                headers: {}
            })
                .then(this._handleFetchResponse)
                .then(data => {
                    console.log("Usuários recebidos:", data);
                    this.populateUserSelect(data);
                })
                .catch(error => {
                    console.error('Erro ao buscar usuários:', error);
                });
        },

        populateUserSelect: function (data) {
            const $userSelect = this.$('#userSelect');
            $userSelect.empty();
            data.forEach(user => {
                $userSelect.append(new Option(user.name, user.id));
            });
        },

        _sendReportToUsers: function (reportId, userIds) {
            console.log("Enviando relatório com ID:", reportId, "para os usuários:", userIds);

            const element = this.$('.card-body')[0];
            const opt = {
                margin: 0.3,
                filename: 'relatorio.pdf',
                image: {type: 'jpeg', quality: 0.98},
                html2canvas: {scale: 2},
                jsPDF: {unit: 'in', format: 'a4', orientation: 'portrait'}
            };

            html2pdf().from(element).toPdf().output('datauristring').then((pdfBase64) => {
                const pdfData = pdfBase64.split(',')[1];

                console.log({
                    report_id: reportId,
                    user_ids: userIds,
                    pdf_blob: pdfData,
                });

                const payload = JSON.stringify({
                    report_id: reportId,
                    user_ids: userIds,
                    pdf_blob: pdfData,
                });

                fetch('/report/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: payload,
                })
                    .then(response => {

                        if (!response.ok) {
                            throw new Error(`Erro na resposta do servidor: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Relatório enviado com sucesso:", data);
                    })
                    .catch(error => {
                        console.error('Erro ao enviar o relatório:', error);
                    });
            });
        }
        ,

        populateReportTypes: function (data) {
            const $reportSelect = this.$('#revenueTypes');
            $reportSelect.empty().append(new Option('Selecione um relatório', ''));
            data.forEach(report => {
                $reportSelect.append(new Option(report.name, report.id));
            });
            $reportSelect.trigger('change');
        },

        _setupEventListeners: function () {
            this.$('#applyButton').on('click', () => {
                const selectedValue = this.$('#revenueTypes').val();
                if (selectedValue) {
                    this._fetchReportData(selectedValue);
                } else {
                    console.error('Nenhum relatório selecionado.');
                }
            });

            this.$('.enviar').on('click', () => {
                console.log("Botão 'Enviar' clicado");
                this._fetchOdooUsers();
                $('#sendModal').modal('show');
            });

            this.$('#sendReportButton').on('click', () => {
                const selectedUsers = this.$('#userSelect').val();
                const selectedReport = this.$('#revenueTypes').val();
                if (selectedUsers && selectedReport) {
                    this._sendReportToUsers(selectedReport, selectedUsers);
                } else {
                    console.error('Nenhum usuário ou relatório selecionado.');
                }
            });

            this.$('.btn-download').on('click', () => {
                const selectedValue = this.$('#revenueTypes').val();
                if (selectedValue) {
                    this.downloadPDF();
                } else {
                    console.error('Nenhum relatório selecionado para download.');
                }
            });

            this.$('.fechar').on('click', () => {
                console.log("Modal fechado");
                $('#sendModal').modal('hide');
            });

        },

        downloadPDF: function () {
            const element = this.$('.card-body')[0];
            const divToHide = this.$('.d-print-none')[0];
            const originalDisplay = divToHide.style.display;

            divToHide.style.display = 'none';

            const opt = {
                margin: 0.3,
                filename: 'relatorio.pdf',
                image: {type: 'jpeg', quality: 0.98},
                html2canvas: {scale: 2},
                jsPDF: {unit: 'in', format: 'a3', orientation: 'portrait'}
            };

            html2pdf().from(element).set(opt).save().then(() => {
                divToHide.style.display = originalDisplay;
            }).catch((error) => {
                console.error("Erro ao gerar o PDF:", error);
                divToHide.style.display = originalDisplay;
            });

        },


        _fetchReportData: function (reportId) {
            console.log("Buscando dados do relatório com ID:", reportId);
            fetch(`/report/subcontas/${reportId}`, {
                method: 'GET',
                headers: {}
            })
                .then(this._handleFetchResponse)
                .then(data => {
                    console.log("Dados do relatório recebidos:", data);
                    if (data && data.subcontas) {
                        this.appendToTable(data.subcontas);
                        this.populateInvoiceData(data);
                        this.appendTotal(this.$('.report-container'), data);
                    } else {
                        console.error('Esperado um objeto com subcontas, mas recebeu:', data);
                    }
                })
                .catch(error => {
                    console.error('Erro ao buscar dados do relatório:', error);
                });
        },


        appendToTable: function (subcontas) {
            const $reportContainer = this.$('.report-container');
            $reportContainer.empty();
            let totalGeneral = 0;

            subcontas.forEach((subconta, subIndex) => {
                let totalAmount = this.appendSubcontaToTable(subconta, subIndex);
                totalGeneral += totalAmount;
            });

            this.appendTotalRow($reportContainer, totalGeneral);
        },

        appendSubcontaToTable: function (subconta, subIndex) {
            let $reportContainer = this.$('.report-container');
            let totalAmount = 0;

            let operationSymbol = subconta.operation_type === "add" ? "+" : subconta.operation_type === "subtract" ? "-" : "";
            let subcontaTitle = `<h5 class="font-weight-bolder"> (${operationSymbol}) ${subconta.name} </h5>`;
            $reportContainer.append(subcontaTitle);


            let subcontaTable = `
                <div class="table-responsive mb-5">
                    <table class="table align-middle table-nowrap table-centered mb-4">
                        <thead>
                            <tr>
                                <th style="width: 70px;">No.</th>
                                <th>Item</th>
                                <th>Amount</th>
                                <th>Ano</th>
                                <th class="text-end" style="width: 120px;">Total</th>
                            </tr>
                        </thead>
                        <tbody class="report-table-body-${subIndex}"></tbody>
                    </table>
                </div>
            `;
            $reportContainer.append(subcontaTable);

            if (subconta.items && subconta.items.length > 0) {
                subconta.items.forEach((item, itemIndex) => {
                    totalAmount += parseFloat(item.amount);
                    this.appendItemRow(subIndex, item, itemIndex, totalAmount);
                });
            }

            this.appendSubtotalRow(subIndex, totalAmount);
            return totalAmount;
        },

        appendItemRow: function (subIndex, item, itemIndex, totalAmount) {
            let itemRow = `
                <tr>
                    <th scope="row">${itemIndex + 1}</th>
                    <td>
                        <div>
                            <h5 class="text-truncate font-size-14 mb-1">${item.item_name}</h5>
                            <p class="text-muted mb-0">${item.item_name}</p>
                        </div>
                    </td>
                    <td>$ ${item.amount}</td>
                    <td>${item.create_date || 'N/A'}</td>
                    <td class="text-end">$ ${totalAmount.toFixed(2)}</td>
                </tr>
            `;
            this.$(`.report-table-body-${subIndex}`).append(itemRow);
        },

        appendSubtotalRow: function (subIndex, totalAmount) {
            let subtotalRow = `
                <tr>
                    <th scope="row" colspan="4" class="text-end">Sub Total</th>
                    <td class="text-end">$ ${totalAmount.toFixed(2)}</td>
                </tr>
            `;
            this.$(`.report-table-body-${subIndex}`).append(subtotalRow);
        },

        appendTotalRow: function ($reportContainer, totalGeneral) {
            let totalRow = `
                <div class="table-responsive d-none">
                    <p class="mb-0">Total Geral:</p
                    <p>$ ${totalGeneral.toFixed(2)}</p>
                </div>
            `;
            $reportContainer.append(totalRow);
        },

        appendTotal: function ($reportContainer, data) {
            let totalRow = `
                <div class="table-responsive ">
                    <p class="mb-0 fw-bolder-7 fa-2x">Total Geral:</p
                    <p class="mb-0 fw-bolder-7 fa-2x fs-3">$ ${data.total_balance}</p>
                </div>
            `;
            $reportContainer.append(totalRow);
        },


        _handleFetchResponse: function (response) {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        },

        populateInvoiceData: function (data) {
            this.$('.invoice-number').text(data.order_number || 'N/A');
            this.$('.invoice-date').text(new Date(data.create_date).toLocaleDateString() || 'N/A');
            this.$('.order-number').text(data.order_number || 'N/A');
            this.$('.order-number').text('#' + data.order_number || 'N/A');
            this.$('.create_uid').text('#' + data.create_uid || 'N/A');
            this.$('.email').text('E-mail: ' + data.login || 'N/A');
            // this.$('.total').text(data.total_balance || 'N/A');
        },

    });

    core.action_registry.add('reportar', Tablereport);
    return Tablereport;
});
``