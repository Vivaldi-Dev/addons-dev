/** @odoo-module **/
import {
    registerInstancePatchModel,
    registerFieldPatchModel,
    registry
} from '@mail/model/model_core';
import Dialog from "web.Dialog";
const { _t } = require('web.core');
const composer_view = registry['mail.composer_view']
import { one2one } from '@mail/model/model_field';

var recorder, gumStream;

registerInstancePatchModel('mail.composer_view', 'mail/static/src/models/composer_view/composer_view.js', {
    recordVoice: function() {
        var self = this;
        if (recorder && recorder.state == "recording") {
            recorder.stop();
            gumStream.getAudioTracks()[0].stop();
        } else {
            var audioElements = $('.o_attachment_audio');
            audioElements.each(function(index, element) {
                for (let i = 0; i < element.children.length; i++) {
                    element.children[i].pause();
                }
            });

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then((stream) => {
                    gumStream = stream;
                    recorder = new MediaRecorder(stream);
                    recorder.ondataavailable = async function(event) {
                        var reader = new FileReader();
                        reader.readAsDataURL(event.data);
                        reader.onloadend = async function() {
                            var data = reader.result;
                            var fl = [];
                            var array = data.split(','),
                                mime = array[0].match(/:(.*?);/)[1],
                                bstr = atob(array[1]),
                                n = bstr.length,
                                u8arr = new Uint8Array(n);

                            while (n--) {
                                u8arr[n] = bstr.charCodeAt(n);
                            }

                            var voice_file = new File([u8arr], 'message.mp3', { type: mime });
                            fl.push(voice_file);
                            await self._fileUploaderRef.comp.uploadFiles(fl);
                        };
                    };
                    recorder.start();
                })
                .catch((err) => {
                    console.error("Erro ao acessar o microfone:", err);
                });
        }
    },
});

/**
 * Registers a field patch model for the 'mail.attachment' model.
 */
registerFieldPatchModel('mail.attachment', 'mail/static/src/models/attachment/attachment.js', {
    attachment: one2one('mail.attachmentAudio', {
        inverse: 'attachment',
        isCausal: true,
    }),
});