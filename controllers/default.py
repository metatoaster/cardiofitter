# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def index():
    return dict(message=T('Fitter'))

def fitter_form():
    """
    Show the fitting form.
    """

    return dict()

    # This is the alternative way of generating the form.

    '''
    form = FORM(
        LABEL("Enter the URI to the following meshes:", _for="mesh.name"),
        INPUT(_name="mesh.name"),

        FIELDSET(
            LEGEND("Epicardial"),
            LABEL("DS", _for="epi.ds"),
            INPUT(_name="epi.ds"),
            LABEL("ES", _for="epi.es"),
            INPUT(_name="epi.es"),
            LABEL("ED", _for="epi.ed"),
            INPUT(_name="epi.ed"),
        ),

        FIELDSET(
            LEGEND("Endocardial"),
            LABEL("DS", _for="endo.ds"),
            INPUT(_name="endo.ds"),
            LABEL("ES", _for="endo.es"),
            INPUT(_name="endo.es"),
            LABEL("ED", _for="endo.ed"),
            INPUT(_name="endo.ed"),
        ),

        INPUT(_type='submit'),

        _action='fitting',  # redirect to the bottom method
    )

    return dict(form=form)
    '''

def fitting():

    from os.path import normpath, join, exists, dirname
    from os import mkdir
    from shutil import copy
    import json

    from bioeng.epiendofitting.manager import ProjectBase
    from bioeng.epiendofitting.main import run_remote_source
    form = FORM()

    if 'mesh.name' not in request.vars:
        raise HTTP(400)

    project = ProjectBase()
    project.createProject(request.vars['mesh.name'])

    # Check whether destination exists
    uploadpath = normpath(join(dirname(__file__), '..', 'uploads'))
    cached = exists(join(uploadpath, project.safename))

    sp = ['DS', 'ES', 'ED']
    op = {}
    result = {}
    for i in sp:
        result[i] = []

    if not cached:
        run_remote_source(project,
            endo_ds=request.vars['endo.ds'],
            endo_ed=request.vars['endo.ed'],
            endo_es=request.vars['endo.es'],
            epi_ds=request.vars['epi.ds'],
            epi_ed=request.vars['epi.ed'],
            epi_es=request.vars['epi.es'],
        )

        # create project space.
        mkdir(join(uploadpath, project.safename))
        for i in sp:
            op[i] = join(uploadpath, project.safename, i)
            mkdir(op[i])

    # only the DS files are generated.

    ds_f = [
        'BackTransformedUPFFinalRotated_Endo.exdata',
        'BackTransformedUPFFinalRotated_Epi.exdata',
        'fitted_epi_humanLV.exelem',
        'fitted_epi_humanLV.exnode',
        'LVCanineModel_Transformed_EndoTrans.exelem',
        'LVCanineModel_Transformed_EndoTrans.exnode',
    ]
    for i in ds_f:
        result['DS'].append(i)
        if cached:
            # already copied.
            continue
        dst = join(op['DS'], i)
        src = project.getSubpath('geometric_model', i)
        copy(src, dst)

    project.destroyProject()
    json_r = json.dumps({
        'fileroot': URL('download', args=[project.safename]),
        'files': result,
    })

    return json_r


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    import os.path
    from os.path import join, normpath, dirname

    uploadroot = normpath(join(dirname(__file__), '..', 'uploads'))

    # eliminate traversal attack
    subpath = normpath(join(os.path.sep, *request.args))
    target = uploadroot + subpath

    if not os.path.isfile(target):
        raise HTTP(403)

    try:
        fd = open(target)
    except:
        raise HTTP(403)

    result = fd.read()
    fd.close()

    return result


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
