/** @odoo-module **/

import publicWidget from 'web.public.widget';


publicWidget.registry.Dynamic = publicWidget.Widget.extend({
    selector: '.DashboarD',

    /**
     * @override
     */
    start() {

            console.log("Chegou chegou")
            console.log( this.el.querySelector('#rowto'))
            console.log( this.el.querySelector('#tabela'))
            let row = this.el.querySelector('#rowto')
            let table = this.el.querySelector('#tabela')
               let countwhite = 0
               let countyellow = 0
               let countred = 0
            if(row){

                this._rpc({
                route:'/banco_teste/',
                params:{}

                }).then(data => {
                    console.log(data)

                        let htmlv2=``

                      let html = `
                            <thead>
                                <tr>
                                    <th scope="col" width="50">#</th>
                                    <th scope="col">Nome da Requisicao</th>
                                    <th scope="col">Data</th>
                                    <th scope="col">Tecnico Residente</th>
                                    <th scope="col">Eg.Responsavel</th>
                                    <th scope="col">Task</th>
                                    <th scope="col">Project</th>
                                    <th scope="col">status</th>



                                </tr>
                            </thead>
                            <tbody>`;


                       data.data.forach(dados =>{
                        data.data.sort((a, b) => a.id - b.id);
                        console.log(dados)



                        // Calcular a diferença de dias entre a data atual e a data fornecida
                                let today = new Date();
                                let dataRequisicao = new Date(dados.date);
                                let diffTime = (dataRequisicao - today );
                                let diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                                 let red ='#FF9999'
                                 let yellow ='#FFFF99'
                                 let white = '#fff'


                                console.log(diffDays)
                                    let cor = '';
                                if(diffDays < 2){

                                     cor = '#FF9999';
                                        countred += 1;

                                }else if(diffDays < 3){
                                   cor = '#FFFF99';
                                   countyellow += 1;
                                }else{
                                    cor='';
                                    countwhite += 1;
                                }



                            htmlv2 = `

                            <div class="col-md-4 ">
                                    <div class="p-3 bg-white shadow-sm d-flex justify-content-around align-items-center box">
                                        <div>
                                            <h3 class="fs-2">${dados.total_requisitions}</h3>
                                            <p class="fs-5">Total Requisitado</p>
                                        </div>

                                         <i class=" primary-text border rounded-full secondary-bg p-3"> <img style="width: 40px;" src="/portalinherit/static/src/img/total-icon.png" alt=""></i>

                                    </div>
                            </div>

                                <div class="col-md-4 ">
                                    <div class="p-3 customyellow shadow-sm d-flex justify-content-around align-items-center  box">
                                        <div>
                                            <h3 class="fs-2">${countyellow}</h3>
                                            <p class="fs-5">Total Em Atraso</p>
                                        </div>

                                            <i class=" primary-text border rounded-full secondary-bg p-3"> <img style="width: 40px;" src="/portalinherit/static/src/img/calendario.png" alt=""></i>
                                    </div>
                                </div>

                                <div  class="col-md-4 ">
                                    <div class="p-3 customred shadow-sm d-flex justify-content-around align-items-center  box1">
                                        <div>
                                            <h3 class="fs-2">${countred}</h3>
                                            <p class="fs-5">Total delongado</p>
                                        </div>
                                         <i class=" primary-text border rounded-full secondary-bg p-3"> <img style="width: 40px;" src="/portalinherit/static/src/img/relogio.png" alt=""></i>

                                    </div>
                                </div>


                                `




                        html += `

                                        <tr style="background-color: ${cor};">
                                            <th scope="row">${dados.id}</th>
                                            <td>${dados.name}</td>
                                            <td>${dados.date}</td>
                                            <td>${dados.tecnico_residente}</td>
                                             <td>${dados.engenheiros_responsaveis}</td>
                                              <td>${dados.task}</td>
                                              <td>${dados.project}</td>
                                              <td>${dados.status}</td>


                                        </tr>`

                       })

                        table.innerHTML =  html
                        rowto.innerHTML =  htmlv2

                })
            }
       },
});

export default publicWidget.registry.Dynamic;
