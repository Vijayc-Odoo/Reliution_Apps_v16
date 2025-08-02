# -*- coding: utf-8 -*-
import base64
import logging
from odoo import models, fields, api, _

_LOGGER = logging.getLogger("##### Dynamic Backend Theme UI #####")


class DynamicColors(models.TransientModel):
    _name = "dynamic.colors"
    _description = 'Dynamic Color Picker for backend theme'

    # SCSS Class for set dynamic colors
    SCSS_TEMPLATE = """

        body {{
            color: {text_color};
        }}

       .o_main_navbar > a:hover, .o_main_navbar > a:focus, .o_main_navbar > button:hover, .o_main_navbar > button:focus {{
            background-color: {nav_hover} !important;
        }}
       
       .o_main_navbar > ul > li > a:hover, .o_main_navbar > ul > li > label:hover {{
            background-color: {nav_hover} !important;
        }}
       
       .o_main_navbar > ul > li > a:hover, .o_main_navbar > ul > li > label:hover {{
            color: {nav_hover_fontcolor} !important;
        }}

       .o_main_navbar {{
            background-color: {nav_background} !important;
            color: {nav_fontcolor} !important;
        }}
        
       .o_main_navbar .dropdown .dropdown-toggle, 
       .o_main_navbar .o_menu_sections .dropdown .dropdown-toggle, 
       .o_main_navbar .o_menu_systray .dropdown .dropdown-toggle, 
       .o_main_navbar .o_nav_entry, .o_main_navbar .o_menu_sections .o_nav_entry, 
       .o_main_navbar .o_menu_systray .o_nav_entry, 
       .o_main_navbar > .o_menu_sections > div, 
       .o_main_navbar > .o_menu_sections > div > a, 
       .o_main_navbar .o_menu_systray > div, 
       .o_main_navbar .o_menu_systray > div > a, 
       .o_main_navbar .o_menu_toggle, 
       .o_main_navbar .o_navbar_apps_menu {{
            background-color: {nav_background} !important;
            color: {nav_fontcolor} !important;
        }}
        
      .o_list_view .o_list_table thead {{
            background-color: {nav_background} !important;
            color: {nav_fontcolor} !important;
        }}
        
      .o_list_view .o_list_table tfoot {{
            background-color: {nav_background} !important;
            color: {nav_fontcolor} !important;
        }}         

      .o_main_navbar > ul > li > a, .o_main_navbar > ul > li > label {{
            color: {nav_fontcolor} !important;
        }}

      .btn-primary {{
            color: {btn_pri_fontcolor};
            background-color: {btn_pri_background};
        }}

      .o_home_menu_background {{
            background:{home_ee_background}!important;
        }}
        
      .o_searchview .o_searchview_facet .o_searchview_facet_label {{
            background-color: {nav_hover_fontcolor} !important;
        }}
        
    """

    URL = '/dynamic_backend_ui_cqt/static/src/scss/colors.scss'

    home_ee_background = fields.Char(default="")
    text_color = fields.Char(string="Basic Text Color", default="")
    nav_background = fields.Char(string="Navigation Background", default="")
    nav_fontcolor = fields.Char(string="Navigation Fontcolor", default="")
    nav_hover = fields.Char(string="Navigation Hover Background", default="")
    nav_hover_fontcolor = fields.Char(string="Navigation Hover Font", default="")
    btn_pri_background = fields.Char(string="Button Backgroundcolor", default="")
    btn_pri_fontcolor = fields.Char(string="Button Fontcolor", default="")

    # Save button method
    def execute(self):

        self.env['ir.config_parameter'].set_param("nav_background", self.nav_background)
        self.env['ir.config_parameter'].set_param("home_ee_background", self.home_ee_background)
        self.env['ir.config_parameter'].set_param("nav_fontcolor", self.nav_fontcolor)
        self.env['ir.config_parameter'].set_param("nav_hover", self.nav_hover)
        self.env['ir.config_parameter'].set_param("nav_hover_fontcolor", self.nav_hover_fontcolor)
        self.env['ir.config_parameter'].set_param("text_color", self.text_color)
        self.env['ir.config_parameter'].set_param("btn_pri_background", self.btn_pri_background)
        self.env['ir.config_parameter'].set_param("btn_pri_fontcolor", self.btn_pri_fontcolor)
        self.update_scss_dynamic_attachment()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def default_get(self, fields):

        if self.env['ir.config_parameter'].get_param("home_ee_background"):
            home_ee_background = self.env['ir.config_parameter'].get_param("home_ee_background")
        else:
            home_ee_background = '#000000'

        if self.env['ir.config_parameter'].get_param("nav_background"):
            nav_background = self.env['ir.config_parameter'].get_param("nav_background")
        else:
            nav_background = '#1141d4'

        if self.env['ir.config_parameter'].get_param("nav_fontcolor"):
            nav_fontcolor = self.env['ir.config_parameter'].get_param("nav_fontcolor")
        else:
            nav_fontcolor = '#ffffff'

        if self.env['ir.config_parameter'].get_param("nav_hover"):
            nav_hover = self.env['ir.config_parameter'].get_param("nav_hover")
        else:
            nav_hover = '#167d25'

        if self.env['ir.config_parameter'].get_param("nav_hover_fontcolor"):
            nav_hover_fontcolor = self.env['ir.config_parameter'].get_param("nav_hover_fontcolor")
        else:
            nav_hover_fontcolor = '#ffffff'

        if self.env['ir.config_parameter'].get_param("text_color"):
            text_color = self.env['ir.config_parameter'].get_param("text_color")
        else:
            text_color = '#000000'

        if self.env['ir.config_parameter'].get_param("btn_pri_background"):
            btn_pri_background = self.env['ir.config_parameter'].get_param("btn_pri_background")
        else:
            btn_pri_background = '#000000'

        if self.env['ir.config_parameter'].get_param("btn_pri_fontcolor"):
            btn_pri_fontcolor = self.env['ir.config_parameter'].get_param("btn_pri_fontcolor")
        else:
            btn_pri_fontcolor = '#ffffff'

        res = {
            "home_ee_background": home_ee_background,
            "nav_background": nav_background,
            "nav_fontcolor": nav_fontcolor,
            "nav_hover": nav_hover,
            "nav_hover_fontcolor": nav_hover_fontcolor,
            "text_color": text_color,
            "btn_pri_background": btn_pri_background,
            "btn_pri_fontcolor": btn_pri_fontcolor
        }
        return res

    # To set dynamic scss class
    def update_scss_dynamic_attachment(self):

        ir_attachment_objs = self.env['ir.attachment']
        parameters = self.sudo().default_get([])
        scss_data = self.SCSS_TEMPLATE.format(**parameters)
        datas = base64.b64encode(scss_data.encode('utf-8'))
        attachment_id = ir_attachment_objs.sudo().search([('url', 'like', self.URL)])
        values = {
            'datas': datas,
            'url': self.URL,
            'name': self.URL,
            'type': 'binary',
            'mimetype': 'text/scss',
        }
        if attachment_id:
            attachment_id.sudo().write(values)
        else:
            attachment_id = ir_attachment_objs.sudo().create(values)
        _LOGGER.info(f"Dynamic Backend Theme SCSS Attachment : {attachment_id.ids}")
        self.env['ir.qweb'].sudo().clear_caches()
        return self.URL
