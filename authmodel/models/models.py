# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.authmodel.utils import random_token

EXPIRE_TOKEN = True
time_expire_token_in_minutes = 24 * 60
time_expire_refresh_in_minutes = 144 * 60

class authmodel(models.Model):
    _name = 'authmodel.authmodel'
    _description = 'authmodel.authmodel'

    user_id = fields.Many2one("res.users", string="User", required=True)
    token = fields.Char("Access Token", required=True)
    refresh = fields.Char("Refresh Token", required=True)

    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)
    refresh_expiry_date = fields.Datetime(string="Refresh Expiry Date", required=True)
    device = fields.Char("Device ID")

    scope = fields.Char(string="Scope")

    def find_or_create_token(self, user_id=None, device=None, create=False):
        _logger = logging.getLogger(__name__)
        _logger.info("find_or_create_token chamado com: user_id=%s, device=%s, create=%s", user_id, device, create)

        print("find_or_create_token chamado com: user_id=%s, device=%s, create=%s", user_id, device, create)

        if not user_id:
            user_id = self.env.user.id

        access_token = self.env['authmodel.authmodel'].sudo().search(
            [("user_id", "=", user_id), ("device", "=", device)], order="id DESC", limit=1)

        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None

        if not access_token and create:
            token_expiry_date = datetime.now() + timedelta(minutes=time_expire_token_in_minutes)
            refresh_expiry_date = datetime.now() + timedelta(minutes=time_expire_refresh_in_minutes)
            vals = {
                "user_id": user_id,
                "device": device,
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "refresh_expiry_date": refresh_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": random_token(prefix='access'),
                "refresh": random_token(prefix='refresh'),
                "scope": "userinfo",
            }
            _logger.info("Criando novo token com valores: %s", vals)
            access_token = self.env['authmodel.authmodel'].sudo().create(vals)

        return access_token

    def is_valid(self, scopes=None):
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        if not EXPIRE_TOKEN:
            return False
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)

    def has_refresh_expired(self):
        if not EXPIRE_TOKEN:
            return False
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.refresh_expiry_date)

    def refresh_token(self):

        token_expiry_date = datetime.now() + timedelta(minutes=time_expire_token_in_minutes)
        refresh_expiry_date = datetime.now() + timedelta(minutes=time_expire_refresh_in_minutes)
        json = {
            "user_id": self.user_id,
            "device": self.device,
            "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "refresh_expiry_date": refresh_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "token": random_token(prefix='access{}'.format(self.device)),
            "refresh": random_token(prefix='refresh{}'.format(self.device), length=60),
            "scope": "userinfo",
        }
        self.write(json)
        return self

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

    @api.model
    def cleanup_expired_tokens(self, _logger=None):
        """Remove tokens cujo prazo de validade expirou."""
        expired_tokens = self.sudo().search([
            '|',
            ('token_expiry_date', '<', fields.Datetime.now()),
            ('refresh_expiry_date', '<', fields.Datetime.now())
        ])
        if expired_tokens:
            expired_tokens.unlink()
            print("Tokens expirados removidos: %s", len(expired_tokens))



class Users(models.Model):
    _inherit = "res.users"
    token_ids = fields.One2many('authmodel.authmodel', "user_id", string="Access Tokens")