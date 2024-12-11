odoo.define('irps.mapa', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    function loadHtml2Pdf() {
        return new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
            script.onload = () => resolve(script);
            document.head.appendChild(script);
        });
    }

    function formatAsCurrency(value) {
        if (isNaN(value) || value == null) {
            return '0.00 ';
        }
        return new Intl.NumberFormat('pt-MZ', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    const mapairps = AbstractAction.extend({

        template: 'ipsreport',

        start: function () {
            this._super.apply(this, arguments);
            loadHtml2Pdf().then(() => {
                this._fetchMpaDeIrps();
                this._setupEventListeners();
            });
        },

         _setupEventListeners: function () {
            this.$('.btn-download').on('click', this.downloadPDF.bind(this));
            this.$('.btn-download-excel').on('click', this.downloadExcel.bind(this));
        },

        downloadPDF: function () {
            console.log("Botão de download clicado.");

            const element = document.querySelector('.body-panel');
            if (!element) {
                console.error("Elemento não encontrado.");
                return;
            }
            console.log("Elemento .container encontrado:", element);

            const opt = {
                margin: 0.2,
                filename: 'relatorio.pdf',
                image: {type: 'jpeg', quality: 0.98},
                html2canvas: {scale: 2},
                jsPDF: {unit: 'in', format: 'a4', orientation: 'landscape'}
            };
            console.log("Configuração do PDF:", opt);

            const divToHide = this.$('.d-print-none')[0];
            if (divToHide) {
                const originalDisplay = divToHide.style.display;
                divToHide.style.display = 'none';

                html2pdf().from(element).set(opt).save()
                    .then(() => {
                        console.log("PDF gerado e baixado com sucesso.");
                        divToHide.style.display = originalDisplay;
                    })
                    .catch((error) => {
                        console.error("Erro ao gerar o PDF:", error);
                        divToHide.style.display = originalDisplay;
                    });
            } else {
                html2pdf().from(element).set(opt).save()
                    .then(() => {
                        console.log("PDF gerado e baixado com sucesso.");
                    })
                    .catch((error) => {
                        console.error("Erro ao gerar o PDF:", error);
                    });
            }
        },

        downloadExcel: function () {
            console.log("Botão de download do Excel clicado.");

            fetch('/mapa/excel/', {
                method: 'POST',
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Erro ao gerar o Excel.');
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'Mapa de IRPS.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    console.log('Download do Excel concluído.');
                })
                .catch(error => {
                    console.error('Erro ao baixar o Excel:', error);
                });
        },


        _fetchMpaDeIrps: function () {
            console.log("Buscando ...");

            const actionParams = (this.props && this.props.context && this.props.context.params) || {};
            const registroId = actionParams.id;

            const hashString = window.location.hash;
            let idFromHash = null;
            if (hashString) {
                const params = new URLSearchParams(hashString.replace('#', ''));
                idFromHash = params.get('id');
                console.log(idFromHash);
            }

            const idToUse = idFromHash || registroId;
            if (!idToUse) {
                console.error("ID não encontrado.");
                return;
            }

            console.log(idToUse);

            fetch(`/mapa/mapa/${idToUse}`, {
                method: 'GET',
                headers: {}
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Resposta da API:', data);
                    if (data.error) {
                        console.error("Erro no servidor:", data.error);
                        return;
                    }

                     document.getElementById('company_name').textContent = `Empresa: ${data.company}`;


                     const meses = [
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ];

                    const mesNome = meses[parseInt(data.month) - 1];

                    const anoAtual = new Date().getFullYear();

                    document.getElementById('mes').textContent = `Mês: ${mesNome} ${anoAtual}`


                    const tableBody = document.getElementById('irps');
                    tableBody.innerHTML = '';

                    data.aggregated_salary_rule_lines.forEach((rule) => {
                        const row = document.createElement('tr');

                        row.innerHTML = `
                    <td>${rule.codigo_funcionario}</td>
                    <td>${rule.employee_id}</td>
                    <td>${rule.numero_contribuinte}</td>
                    <td>${rule.numero_beneficiario}</td>
                    <td>${formatAsCurrency(rule.irps_amout)}</td>
                `;

                        tableBody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Erro ao buscar os dados:', error);
                });
        },


    });


    core.action_registry.add('irps', mapairps);

    return mapairps;
});
