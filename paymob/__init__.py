from . import models
from . import controllers
from . import wizard

import odoo.addons.payment as payment


def post_init_hook(env):
    payment.setup_provider(env, "paymob")


def uninstall_hook(env):
    payment.reset_payment_provider(env, "paymob")
