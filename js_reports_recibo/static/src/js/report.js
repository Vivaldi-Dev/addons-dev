odoo.define('folhareport.folhas', function (require) {
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

    const folhapamento = AbstractAction.extend({

        template: 'folhareport',
        orientation: 'portrait',

        start: function () {
            this._super.apply(this, arguments);
            loadHtml2Pdf().then(() => {
                this._fetchFolhaDePagamento();
                this._setupEventListeners();
                console.log("Novos dados sendo buscados...");
            });
        },

        _setupEventListeners: function () {
            this.$('.btn-download').on('click', this.downloadPDF.bind(this));
            this.$('.btn-toggle-orientation').on('click', this.toggleOrientation.bind(this));
            this.$('.btn-download-excel').on('click', this.downloadExcel.bind(this));
        },

        toggleOrientation: function () {
            this.orientation = this.orientation === 'portrait' ? 'landscape' : 'portrait';
            console.log("Orientação alterada para:", this.orientation);
        },

        downloadPDF: function () {
            console.log("Botão de download clicado.");

            const element = document.querySelector('.panel-body');
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

                html2pdf().from(element)
                    .set(opt)
                    .save()
                    .then(() => {
                        console.log("PDF gerado e baixado com sucesso.");
                        divToHide.style.display = originalDisplay;
                    })
                    .catch((error) => {
                        console.error("Erro ao gerar o PDF:", error);
                        divToHide.style.display = originalDisplay;
                    });
            } else {
                html2pdf()
                    .from(element)
                    .set(opt)
                    .save()
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

            fetch('/folhapagamento/excel', {
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
                    a.download = 'relatorio.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    console.log('Download do Excel concluído.');
                })
                .catch(error => {
                    console.error('Erro ao baixar o Excel:', error);
                });
        },

        _fetchFolhaDePagamento: function () {
            console.log("Buscando relatórios disponíveis...");

            const actionParams = (this.props && this.props.context && this.props.context.params) || {};
            const registroId = actionParams.id;

            const hashString = window.location.hash;
            let idFromHash = null;
            if (hashString) {
                const params = new URLSearchParams(hashString.replace('#', ''));
                idFromHash = params.get('id');
                console.log(idFromHash)
            }

            const idToUse = idFromHash || registroId;
            if (!idToUse) {
                console.error("ID não encontrado.");
                return;
            }

            console.log(idToUse);

            fetch(`/folhapagamento/data/${idToUse}`, {
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

                    console.log(data.aprovado_por);

                    document.getElementById('company_name').textContent = `Empresa: ${data.company}`;
                    document.getElementById('departament').textContent = `Departamento: ${data.departamento_id}`;

                    const meses = [
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ];

                    const mesNome = meses[parseInt(data.month) - 1];

                    const anoAtual = new Date().getFullYear();

                    document.getElementById('mes').textContent = `Mês: ${mesNome} ${anoAtual}`
                    document.getElementById('mes').style.fontSize = '24px';

                    if (data.aggregated_salary_rule_lines) {
                        const tableBody = document.getElementById('salary-data-body');
                        tableBody.innerHTML = '';

                        let geralIndex = 1;
                        data.aggregated_salary_rule_lines.forEach(rule => {
                            let row = document.createElement('tr');

                            const totalHorasExtras = (rule.horasextrascem || 0) + (rule.horasextrasc || 0);

                            row.innerHTML = `
                            <td class="text-center">${geralIndex}</td>
                            <td class="text-nowrap">${rule.employee_name}</td>
                            <td class="">${rule.job_position}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.basic_amount)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.inc_amount)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(totalHorasExtras)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.totalderemuneracoes)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.inss_amount)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.irps_amout)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.descontoatraso)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.outrosdescontos)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.descotofaltasdias)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.emprestimos)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.fundofunebre)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.totaldedescontos)}</td>
                            <td class="text-right text-nowrap">${formatAsCurrency(rule.net_amount)}</td>
                `;
                            tableBody.appendChild(row);
                            geralIndex++;
                        });

                    } else {
                        console.error('Dados inválidos recebidos:', data);
                    }
                })
                .catch(error => {
                    console.error('Erro ao buscar relatórios:', error);
                });
        }

    });


    core.action_registry.add('folhareport', folhapamento);

    return folhapamento;
});
