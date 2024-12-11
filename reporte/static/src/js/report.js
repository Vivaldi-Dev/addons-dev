odoo.define('reporte.reportes', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    const reportetable = AbstractAction.extend({

            template: 'reportabledynamics',

            start: function () {
                this._super.apply(this, arguments);
                console.log("nova tabela");
                this._fetchData();
                this._bindEvents();
            },

            _bindEvents: function () {
                const self = this;

                // Evento para selecionar uma conta
                this.$('#revenueTypes').on('change', function () {
                    const selectedRevenueId = $(this).val(); // Pega o ID da conta selecionada

                    if (selectedRevenueId) {
                        // Certifique-se de que o selectedRevenueId não seja 'undefined'
                        console.log('ID da conta selecionada:', selectedRevenueId);

                        // Faz a requisição para obter as subcontas associadas
                        self._fetchsubreceita(selectedRevenueId);
                    } else {
                        // Limpa o dropdown de subcontas caso nenhuma conta seja selecionada
                        self.$('#subRevenueType').empty().append('<option value="">Selecione a subconta</option>').prop('disabled', true);
                    }
                });
            },

            _updateTableHeader: function (column, value) {
                if (column === 'Nome') {
                    this.$('th#revenueName').text(value || 'Nome');
                } else if (column === 'Subreceita') {
                    this.$('th#subRevenueTypeName').text(value || 'Tipo de Subreceita');
                }
            },
            _fetchData: function () {
                const self = this;
                console.log("Iniciando a requisição para a API...");

                fetch('/tipo/recita', {
                    method: 'GET',
                    headers: {}
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok: ' + response.status);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("data", data);
                        self._populateRevenueTypeDropdown(data);

                        // Inicializando o Select2 no dropdown de revenueTypes
                        self.$('#revenueTypes').select2({
                            placeholder: 'Selecione ou digite para filtrar...',
                            allowClear: true, // permite limpar a seleção
                            width: 'resolve'  // ajusta a largura automaticamente
                        });
                    })
                    .catch(error => {
                        console.error('Houve um problema com a requisição Fetch:', error);
                    });
            },


            _fetchsubreceita:

                function (accountId) {
                    const self = this;

                    console.log("Iniciando a requisição para a API com o ID da conta:", accountId);

                    fetch(`/subcontas/${accountId}`, {
                        method: 'GET',
                        headers: {}
                    })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok: ' + response.status);
                            }
                            return response.json();
                        })
                        .then(data => {
                            console.log("Subcontas:", data);
                            self._subRevenueTypeDropdown(data);
                        })
                        .catch(error => {
                            console.error('Houve um problema com a requisição Fetch:', error);
                        });
                }

            ,

            _populateRevenueTypeDropdown: function (data) {
                var $revenueTypeDropdown = this.$('#revenueTypes');
                $revenueTypeDropdown.empty().append('<option value="">Selecione a conta</option>');

                data.forEach(function (item) {
                    $revenueTypeDropdown.append('<option value="' + item.id + '">' + item.name + '</option>');
                });
            }
            ,

            _subRevenueTypeDropdown: function (data) {
                const $itemsSelect = this.$('#subRevenueType');
                $itemsSelect.empty();
                $itemsSelect.append(new Option('Selecione a subconta', '', true, true));
                $itemsSelect.prop('disabled', false);

                data.forEach(function (item) {
                    const formattedBalance = `R$ ${item.balance.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                    const itemData = JSON.stringify({name: item.name, balance: formattedBalance});
                    $itemsSelect.append(new Option(`${item.name} - ${formattedBalance}`, itemData));
                });
            }
            ,
        })
    ;

    core.action_registry.add('reporte', reportetable);
    return reportetable;
});
