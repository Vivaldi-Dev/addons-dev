/** @odoo-module **/

import publicWidget from 'web.public.widget';

publicWidget.registry.InitialBalanceWidget = publicWidget.Widget.extend({
    selector: '.initial_balance',

    /**
     * @override
     */
    start() {
        console.log("Thanks God");
        console.log(this.el.querySelector('#finalbalance'));

    },
});

export default publicWidget.registry.InitialBalanceWidget;
