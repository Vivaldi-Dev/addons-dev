/** @odoo-module */

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
import { loadJS } from "@web/core/assets";

const { Component, onMounted } = owl;

export class OwlSalesDashboard extends Component {
    async setup() {
        await this._loadChartLibrary();
    }

    async _loadChartLibrary() {
        try {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            console.log(loadJS)
        } catch (error) {
            console.error("Failed to load Chart.js library", error);
        }
    }

    async mounted() {
        await this._waitForChartElement();


        const data = [
            { year: 2010, count: 10 },
            { year: 2011, count: 20 },
            { year: 2012, count: 15 },
            { year: 2013, count: 25 },
            { year: 2014, count: 22 },
            { year: 2015, count: 30 },
            { year: 2016, count: 28 },
        ];

        new Chart(this.el.querySelector("#chart"), {
            type: 'bar',
            data: {
                labels: data.map(row => row.year),
                datasets: [
                    {
                        label: 'Acquisitions by year',
                        data: data.map(row => row.count)
                    }
                ]
            }
        });
    }

    async _waitForChartElement() {
        // Função para aguardar até que o elemento do gráfico esteja disponível
        return new Promise((resolve) => {
            const checkElement = () => {
                if (this.el.querySelector("#chart")) {
                    resolve();
                } else {
                    setTimeout(checkElement, 100);
                }
            };
            checkElement();
        });
    }
}

OwlSalesDashboard.template = "owl.graph";
OwlSalesDashboard.components = { KpiCard };

registry.category("actions").add("owl.sales_dashboard", OwlSalesDashboard);
