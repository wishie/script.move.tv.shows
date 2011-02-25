# -*- coding: utf-8 -*- 

import sys
import os
import xbmc
import xbmcaddon
import re
import xbmcgui


__scriptid__   = "script.move.tv.shows"
__settings__   = xbmcaddon.Addon(id=__scriptid__)
__language__   = __settings__.getLocalizedString
__version__    = __settings__.getAddonInfo('version')
__cwd__        = __settings__.getAddonInfo('path')
__profile__    = xbmc.translatePath( __settings__.getAddonInfo('profile') )
__scriptname__ = "Move TV Shows"
__author__     = "wishie"

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

directory = __settings__.getSetting( "source" )

dest = []

for x in range(4):
  exec("dest_setting = __settings__.getSetting('dest%s')" % (str(x+1)) )
  if dest_setting != "":
    dest.append(dest_setting)

vid_exts = [".avi", ".mkv", ".wmv", ".divx", ".mp4" ]

season_dirs = ["Season %i",   # eg. Season 1
               "Season %.2d", # eg. Season 01
               ]

def regex_tvshow(file):
    regex_expressions = [ 
                        '[\\\\/\\._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\\/]*)$',
                        '[Ss]([0-9]+)[][._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                        '[\._ \-]([0-9]+)x([0-9]+)([^\\/]*)',
                        '[\._ \-]([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                        '([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                        '[\\\\/\\._ -]([0-9]+)([0-9][0-9])[^\\/]*',
                        'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',
                        '[\\\\/\\._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
                        '[[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',
                        '[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',
                        '[Ss]([0-9]+)[][ ._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                        '[\\._ -]()[Ee][Pp]_?([0-9]+)([^\\\\/]*)$'
                        ]
    
    for x in range(len(regex_expressions)):    
      response_file = re.findall(regex_expressions[x], file)
      if len(response_file) > 0 : 
        log( "Regex File Se: %s, Ep: %s," % (str(response_file[0][0]),str(response_file[0][1]),))
        title = re.split(regex_expressions[x], file)[0]
        for char in ['[', ']', '_', '(', ')','.','-']: 
           title = title.replace(char, ' ')

        title = title.replace("   "," ").replace("  "," ")
        if title.endswith(" "): title = title[:-1]
        return title,response_file[0][0], response_file[0][1]

    return "","", ""  

def copy(file, path):
    try: # Post Dharma
      import xbmcvfs
      size_file, hash_file = xbmc.subHashAndFileSize(file)
      try:
        size_dest, hash_dest = xbmc.subHashAndFileSize(os.path.join(path, os.path.basename(file)))
      except:
        size_dest = 0
        hash_dest = ""
        
      if hash_file != hash_dest: 
        xbmcvfs.copy(file, os.path.join(path, os.path.basename(file)))
      
      if __settings__.getSetting( "delete" ) == "true":
        size_dest, hash_dest = xbmc.subHashAndFileSize(os.path.join(path, os.path.basename(file)))
        if hash_file == hash_dest:
          xbmcvfs.delete(file)
          log("Deleted %s" % file)
          
    except: # Dharma
      import shutil, filecmp
      
      if not os.path.exists(os.path.join(path, os.path.basename(file))):
        shutil.copy(file,os.path.join(path, os.path.basename(file)))
      if filecmp.cmp(file, os.path.join(path, os.path.basename(file))) and __settings__.getSetting( "delete" ) == "true":
        os.remove(file)
        log("Deleted %s" % file)     
    
def search(pDialog):
    copy_list = []
    for root, dirs, files in os.walk(directory, topdown=False):
      file_root = root
      for name in files:
        if (os.path.splitext( name )[1]) in vid_exts:
          try:
            title, season, episode = regex_tvshow(name)
            
            ################ add more cases on here #################
            
            if title == "Law and Order SVU" : title = "Law & Order - Special Victims Unit"
            
            #########################################################
          except:
            title = ""
          if title != "":
            log( "Found [%s], Season [%s] - Episode [%s]" % (title, season, episode))
            file_location = os.path.join(file_root, name)
            for dest_dir in dest:
              directories = os.listdir(dest_dir)
              for d in directories:
                if d.lower() == title.lower():
                  show_path = os.path.join(dest_dir, d)
                  break
              if show_path != "":
                for season_dir in season_dirs:
                  season_dir = os.path.join(show_path, season_dir % int(season))
                  if os.path.exists(season_dir):
                    copy_list.append({'filename':file_location, 'destination':season_dir})
                    pDialog.update(0, __language__(614) % (len(copy_list),))                   
    return copy_list

def log(msg):
  xbmc.output("### [%s] - %s" % (__scriptname__,msg,),level=xbmc.LOGDEBUG ) 

pDialog = xbmcgui.DialogProgress()
ret = pDialog.create(__scriptname__, __language__(610))
pDialog.update(0, __language__(610))
copy_list = search(pDialog)
xbmc.sleep(1000)

x = 1
for item in copy_list: 
  pDialog.update((100/len(copy_list))*x, __language__(612) % (x, len(copy_list)),os.path.basename(item["filename"]) )
  copy(item["filename"],item["destination"])
  x += 1
pDialog.close()

if (len(copy_list) > 0) and (__settings__.getSetting( "scan" ) == "true"):
  xbmc.executebuiltin('UpdateLibrary(video)')
  xbmc.executebuiltin("RunScript(script.recentlyadded,limit=5&albums=True&totals=True)")
