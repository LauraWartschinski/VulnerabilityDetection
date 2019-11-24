################################################################################
# ZMSItem.py
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
################################################################################

# Imports.
from DateTime.DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Persistence import Persistent
from Acquisition import Implicit
import OFS.SimpleItem, OFS.ObjectManager
import zope.interface
# Product Imports.
import IZMSDaemon


################################################################################
################################################################################
###
###   Abstract Class ZMSItem
###
################################################################################
################################################################################
class ZMSItem(
    OFS.ObjectManager.ObjectManager,
    OFS.SimpleItem.Item,
    Persistent,  # Persistent.
    Implicit,    # Acquisition.
    ):

    # Documentation string.
    __doc__ = """ZMS product module."""
    # Version string. 
    __version__ = '0.1' 
    
    # Management Permissions.
    # -----------------------
    __authorPermissions__ = (
      'manage_page_header', 'manage_page_footer', 'manage_tabs', 'manage_main_iframe' 
      )
    __viewPermissions__ = (
      'manage_menu',
      )
    __ac_permissions__=(
      ('ZMS Author', __authorPermissions__),
      ('View', __viewPermissions__),
      )

    # Templates.
    # ----------
    manage = PageTemplateFile('zpt/object/manage', globals())
    manage_workspace = PageTemplateFile('zpt/object/manage', globals())
    manage_main = PageTemplateFile('zpt/ZMSObject/manage_main', globals())
    manage_main_iframe = PageTemplateFile('zpt/ZMSObject/manage_main_iframe', globals())

    # --------------------------------------------------------------------------
    #  ZMSItem.zmi_body_content:
    # --------------------------------------------------------------------------
    def zmi_body_content(self, *args, **kwargs):
      request = self.REQUEST
      response = request.RESPONSE
      return self.getBodyContent(request)

    # --------------------------------------------------------------------------
    #  ZMSItem.zmi_manage_css:
    # --------------------------------------------------------------------------
    def zmi_manage_css(self, *args, **kwargs):
      """ ZMSItem.zmi_manage_css """
      request = self.REQUEST
      response = request.RESPONSE
      response.setHeader('Content-Type','text/css')
      css = []
      for stylesheet in self.getStylesheets():
        try:
          s = stylesheet(self)
        except:
          s = str(stylesheet)
        css.append("/* ######################################################################")
        css.append("   ### %s"%stylesheet.absolute_url())
        css.append("   ###################################################################### */")
        css.append(s)
      return '\n'.join(css)

    # --------------------------------------------------------------------------
    #  ZMSItem.zmi_manage_menu:
    # --------------------------------------------------------------------------
    def zmi_manage_menu(self, *args, **kwargs):
      return self.manage_menu(args,kwargs)

    # --------------------------------------------------------------------------
    #  zmi_body_attrs:
    # --------------------------------------------------------------------------
    def zmi_body_class(self, *args, **kwargs):
      request = self.REQUEST
      l = ['zmi']
      l.append(request['lang'])
      l.extend(map(lambda x:kwargs[x],kwargs.keys()))
      l.append(self.meta_id)
      # FOR EVALUATION: adding node specific css classes [list]
      internal_dict = self.attr('internal_dict')
      if isinstance(internal_dict,dict) and internal_dict.get('css_classes',None):
        l.extend( internal_dict['css_classes'] )
      l.extend(request['AUTHENTICATED_USER'].getRolesInContext(self))
      return ' '.join(l)

    # --------------------------------------------------------------------------
    #  ZMSItem.zmi_page_request:
    # --------------------------------------------------------------------------
    def _zmi_page_request(self, *args, **kwargs):
      for daemon in filter(lambda x:IZMSDaemon.IZMSDaemon in list(zope.interface.providedBy(x)),self.getDocumentElement().objectValues()):
        daemon.startDaemon()
      request = self.REQUEST
      request.set( 'ZMS_THIS',self.getSelf())
      request.set( 'ZMS_DOCELMNT',self.breadcrumbs_obj_path()[0])
      request.set( 'ZMS_ROOT',request['ZMS_DOCELMNT'].absolute_url())
      request.set( 'ZMS_COMMON',getattr(self,'common',self.getHome()).absolute_url())
      request.set( 'ZMI_TIME',DateTime().timeTime())
      request.set( 'ZMS_CHARSET',request.get('ZMS_CHARSET','utf-8'))
      if not request.get('HTTP_ACCEPT_CHARSET'):
        request.set('HTTP_ACCEPT_CHARSET','%s;q=0.7,*;q=0.7'%request['ZMS_CHARSET'])
      if (request.get('ZMS_PATHCROPPING',False) or self.getConfProperty('ZMS.pathcropping',0)==1) and request.get('export_format','')=='':
        base = request.get('BASE0','')
        if request['ZMS_ROOT'].startswith(base):
          request.set( 'ZMS_ROOT',request['ZMS_ROOT'][len(base):])
          request.set( 'ZMS_COMMON',request['ZMS_COMMON'][len(base):])
    
    def zmi_page_request(self, *args, **kwargs):
      request = self.REQUEST
      RESPONSE = request.RESPONSE
      SESSION = request.SESSION
      self._zmi_page_request()
      RESPONSE.setHeader('Expires',DateTime(request['ZMI_TIME']-10000).toZone('GMT+1').rfc822())
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      RESPONSE.setHeader('Content-Type', 'text/html;charset=%s'%request['ZMS_CHARSET'])
      if not request.get( 'preview'):
        request.set( 'preview','preview')
      langs = self.getLanguages(request)
      if request.get('lang') not in langs:
        request.set('lang',langs[0])
      if request.get('manage_lang') not in self.getLocale().get_manage_langs():
        request.set('manage_lang',self.get_manage_lang())
      if not request.get('manage_tabs_message'):
        request.set( 'manage_tabs_message',self.getConfProperty('ZMS.manage_tabs_message',''))
      # manage_system
      if request.form.has_key('zmi-manage-system'):
        request.SESSION.set('zmi-manage-system',int(request.get('zmi-manage-system')))
      # avoid declarative urls
      physical_path = self.getPhysicalPath()
      path_to_handle = request['URL0'][len(request['BASE0']):].split('/')
      path = path_to_handle[:-1]
      if len(filter(lambda x:x.find('.')>0 or x.startswith('manage_'),path))==0:
        for i in range(len(path)):
          if path[:-(i+1)] != physical_path[:-(i+1)]:
            path[:-(i+1)] = physical_path[:-(i+1)]
        new_path = path+[path_to_handle[-1]]
        if path_to_handle != new_path:
          request.RESPONSE.redirect('/'.join(new_path))

    def f_standard_html_request(self, *args, **kwargs):
      request = self.REQUEST
      self._zmi_page_request()
      if not request.get( 'lang'):
        request.set( 'lang',self.getLanguage(request))
      if not request.get('manage_lang') in self.getLocale().get_manage_langs():
        request.set( 'manage_lang',self.get_manage_lang())


    # --------------------------------------------------------------------------
    #  ZMSItem.display_icon:
    #
    #  @param REQUEST
    # --------------------------------------------------------------------------
    def display_icon(self, REQUEST, meta_type=None, key='icon', zpt=None):
      if meta_type is None:
        return self.icon
      else:
        return self.aq_parent.display_icon( REQUEST, meta_type, key, zpt)


    # --------------------------------------------------------------------------
    #  ZMSItem.getTitlealt
    # --------------------------------------------------------------------------
    def getTitlealt( self, REQUEST):
      return self.getZMILangStr( self.meta_type)


    # --------------------------------------------------------------------------
    #  ZMSItem.breadcrumbs_obj_path:
    # --------------------------------------------------------------------------
    def breadcrumbs_obj_path(self, portalMaster=True):
      return self.aq_parent.breadcrumbs_obj_path(portalMaster)

################################################################################