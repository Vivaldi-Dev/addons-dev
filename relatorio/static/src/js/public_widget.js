/** @odoo-module */

import publicWidget from 'web.public.widget';

publicWidget.registry.jstempate = publicWidget.Widget.extend({
    selector: '.jsweb',
    start() {
        console.log("JS template Activated");
        this._super.apply(this, arguments);
    }
});
