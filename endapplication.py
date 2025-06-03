#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
import cast_upgrade_1_6_23  # @UnusedImport
from cast.application import ApplicationLevelExtension, create_link, ReferenceFinder, Bookmark
import logging 
import re
import traceback
import sys

"""
class CortexApplication
"""
    
class CortexApplication(ApplicationLevelExtension):

    ###################################################################################################        

    
    def __init__(self):
        self.dic_cortex_planset = {}
        self.dic_cortex_jobset = {}
        self.dic_jcls_jobsprocs = {}
        self.dic_jobset_2_jcljobproc = {}
        self.dic_jcljobproc_2_jobset = {}
        self.nb_links_created_jobset_2_jcljobproc = 0
        self.nb_links_created_jcljobproc_2_jobset = 0

    ###################################################################################################        

    ###################################################################################################            
    def init_objects_list(self, application):

        logging.info("-------------------------------")
        logging.info("Loading CortexPlanset objects")
        for obj in application.objects().has_type(['CortexPlanset',]):
            #logging.info('  %s|%s' % (obj.get_name(),obj.get_fullname()))        
            key = obj.get_name()
            #key = self.replace_key(obj.get_name())
            self.dic_cortex_planset[key] = obj
            logging.debug("  %s-%s" % (obj.get_name(),obj.get_fullname()))

        logging.info("-------------------------------")
        logging.info("Loading CortexJobset objects")
        for obj in application.objects().has_type(['CortexJobset',]):
            #logging.info('  %s|%s' % (obj.get_name(),obj.get_fullname()))        
            key = obj.get_name()
            #key = self.replace_key(obj.get_name())
            self.dic_cortex_jobset[key] = obj
            logging.debug("  %s-%s" % (obj.get_name(),obj.get_fullname()))

        logging.info("-------------------------------")
        logging.info("Loading JCL Jobs and Procedures objects")
        for obj in application.objects().has_type(['CAST_JCL_Job','CAST_JCL_Procedure',
                                                   'CAST_JCL_CatalogedProcedure', 'CAST_JCL_ProcedurePrototype', 'CAST_JCL_UtilityProcedure', 'CAST_JCL_InstreamProcedure',
                                                   'CAST_JCL_CatalogedJob','CAST_JCL_CatalogedJobPrototype'
        ]):
            #logging.info('  %s|%s' % (obj.get_name(),obj.get_fullname()))        
            key = obj.get_name()
            #key = self.replace_key(obj.get_name())
            self.dic_jcls_jobsprocs[key] = obj
            logging.debug("  %s-%s" % (obj.get_name(),obj.get_fullname()))

    ###################################################################################################
    def end_application(self, application):
        self.process_end_application(application)
    
    def process_end_application(self, application):
        logging.info("*********************************************************************************") 
        logging.info("CortexApplication : running code at the end of an application")

        ################################################################################################
        logging.info("********************************************************************")
        # parsing files when required
        ################################################################################################

        self.init_objects_list(application)
        
        logging.info("** File parsing for .CXPBLINK")
        icount = 0 
        for file in application.get_files():
            icount += 1
            if not file.get_path():
                logging.debug( str(icount)+">checking file # with no path")
                continue
            logging.debug( str(icount)+">checking file > " + file.get_path())
            if re.search('[\.][cC][xX][pP][bB][lL][iI][nN][kK]$', file.get_path()) != None:
                self.scan_pblink_file(file.get_path())

        # shortcut because it's taking to much time to go through all the 100+K files 
        #self.scan_pblink_file(r"C:\Shared\upload\SI_MAINFRAME\main_sources\BATCH\GCONS\CORTEX\GCONS-LST-PDBLINK.CXPBLINK")
        
        logging.info("** Linking Cortex jobsets => JCL Procs and Jobs")
        for jobsetname in self.dic_jobset_2_jcljobproc:
            set_mapping = self.dic_jobset_2_jcljobproc[jobsetname]
            o_jobset = None
            try:
                o_jobset = self.dic_cortex_jobset[jobsetname]
            except KeyError:
                logging.warning("  couldn't find reference for Cortex Jobset %s;having JCL successors %s" % (jobsetname, str(set_mapping) ))
            
            if o_jobset:
                for jcljobprocname in set_mapping:
                    o_jcljobproc = None
                    try:
                        o_jcljobproc = self.dic_jcls_jobsprocs[jcljobprocname]
                    except KeyError:
                        logging.warning("  couldn't find reference for jcljobproc %s;use link with jobset %s" % (jcljobprocname,jobsetname))
                    if o_jcljobproc:
                        logging.info("  Creating link between %s %s and %s %s" % ("Cortex jobset", jobsetname, "JCL Job or JCL Procedure", jcljobprocname))
                        create_link("useLink", o_jobset, o_jcljobproc)
                        self.nb_links_created_jobset_2_jcljobproc += 1
        
        logging.info("** Linking JCL Procs and Jobs => Cortex jobsets ")
        jobsetname, o_jobset, jcljobprocname, o_jcljobproc = None, None, None, None
        for jobsetname in self.dic_jcljobproc_2_jobset:
            set_mapping = self.dic_jcljobproc_2_jobset[jobsetname]
            o_jobset = None
            try:
                o_jobset = self.dic_cortex_jobset[jobsetname]
            except KeyError:
                logging.warning("  couldn't find reference for Cortex Jobset %s;having JCL predecessors %s" % (jobsetname, str(set_mapping)))
            
            if o_jobset:
                for jcljobprocname in set_mapping:
                    o_jcljobproc = None
                    try:
                        o_jcljobproc = self.dic_jcls_jobsprocs[jcljobprocname]
                    except KeyError:
                        logging.warning("  couldn't find reference for jcljobproc %s;use link with jobset %s" % (jcljobprocname,jobsetname))
                    if o_jcljobproc:
                        logging.info("  Creating link between %s %s and %s %s" % ("JCL Job or JCL Procedure", jcljobprocname, "Cortex jobset", jobsetname))
                        create_link("useLink", o_jcljobproc, o_jobset)
                        self.nb_links_created_jobset_2_jcljobproc += 1
    
        self.end_app_log()

    #########################################################################################################################  

    def scan_pblink_file(self, filepath):
        
        logging.debug("INIT scan_pblink_file > " +str(filepath))        
        with open(filepath, 'r') as processing_file:
            i_progress_step = 1000
            iindex = 0
            current_type = None
            current_jobset = None
            for line in processing_file:
                #log.debug("line > " +str(line))        
                iindex += 1 
                result_ignore = re.search(r"^([A-Za-z0-9-])|Licensed material|^[ \t/s]+$", line)
                result_type = re.search(r"CROSS REFERENCES", line)
                result_jobset = re.search(r"^[ ][ ]([A-Za-z0-9*]+)[ \t/s]+(.*)", line)

                type_change = False
                if result_ignore:
                    #log.debug("  ignoring line > " +str(line))        
                    continue
                elif result_type:
                    if '  WAIT' in line:
                        strtype = 'WAIT'
                        type_change = str(current_type) != strtype
                        current_type = strtype
                    elif '  WEAKPRED'  in line:
                        strtype = 'WEAKPRED'
                        type_change = str(current_type) != strtype
                        current_type = strtype
                    elif '  WEAKSUCC' in line:
                        strtype = 'WEAKSUCC'
                        type_change = str(current_type) != strtype
                        current_type = strtype
                    elif '  RESOURCE' in line:
                        strtype = 'RESOURCE'
                        type_change = str(current_type) != strtype
                        current_type = strtype
                    elif '  BYPASS' in line:
                        strtype = 'BYPASS'
                        type_change = str(current_type) != strtype
                        current_type = strtype
                    #log.debug("  ignoring type line (typechange=%s) > %s" % (str(type_change),str(line))) 

                # contains jcl jobs and procs + potentially a jobset (or not if multiline)
                else:
                    str_jcl_jobs_procs = ''
                    if result_jobset:
                        current_jobset = result_jobset.group(1)
                        str_jcl_jobs_procs = result_jobset.group(2)
                        jcls = str_jcl_jobs_procs.split()
                        logging.debug("  jobset %s with jcls %s" % (str(current_jobset),str(jcls))) 
                                
                    else:
                        str_jcl_jobs_procs = line.strip()
                        jcls = str_jcl_jobs_procs.split()
                        logging.debug("  only jcls %s" % (str(jcls))) 
                    
                    if current_jobset and current_type:
                        """for jcl in jcls:
                            if jcl not in self.JCL_JOBS_PROCS:
                                log.warning("  Missing JCL Job or Proc for jobset and type=%s;%s;%s" % (str(jcl),str(current_jobset), str(current_type))) 
                            else:
                                log.debug("  Matching JCL Job or Proc for jobset and type=%s;%s;%s" % (str(jcl),str(current_jobset), str(current_type))) 
                        """        
                        set_mapping = None
                        
                        if current_type in ['WEAKSUCC','WEAKPRED']:
                            if current_type == 'WEAKSUCC':
                                try: 
                                    set_mapping = self.dic_jobset_2_jcljobproc[current_jobset]
                                except KeyError:
                                    self.dic_jobset_2_jcljobproc[current_jobset] = set()
                                    set_mapping = self.dic_jobset_2_jcljobproc[current_jobset]
                                for jclname in jcls:
                                    set_mapping.add(jclname)
                            elif current_type == 'WEAKPRED':
                                try: 
                                    set_mapping = self.dic_jcljobproc_2_jobset[current_jobset]
                                except KeyError:
                                    self.dic_jcljobproc_2_jobset[current_jobset] = set()
                                    set_mapping = self.dic_jcljobproc_2_jobset[current_jobset]
                                for jclname in jcls:
                                    set_mapping.add(jclname)

        logging.debug("dic_jobset_2_jcljobproc=" +str(self.dic_jobset_2_jcljobproc))      
        logging.debug("dic_jcljobproc_2_jobset=" +str(self.dic_jcljobproc_2_jobset))
       
    #########################################################################################################################        
        
    def end_app_log(self):
        # Final reporting
        logging.info("###################################################################################")
        logging.info("End of Cortex Application")
        logging.info("Number of links created between Cortex jobset and JCL Jobs or Procs=%s" % str(self.nb_links_created_jobset_2_jcljobproc))
        logging.info("Number of links created between JCL Jobs or Procs and Cortex jobset=%s" % str(self.nb_links_created_jcljobproc_2_jobset))
        
    #########################################################################################################################
    


