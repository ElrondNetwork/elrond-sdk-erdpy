import logging
from os import path

from erdpy import dependencies, errors, utils, guards
from erdpy.projects import shared
from erdpy.projects.project_clang import ProjectClang
from erdpy.projects.project_cpp import ProjectCpp
from erdpy.projects.project_rust import ProjectRust
from erdpy.projects.project_sol import ProjectSol

logger = logging.getLogger("projects.core")


def load_project(directory):
    guards.is_directory(directory)

    if shared.is_source_clang(directory):
        return ProjectClang(directory)
    if shared.is_source_cpp(directory):
        return ProjectCpp(directory)
    if shared.is_source_sol(directory):
        return ProjectSol(directory)
    if shared.is_source_rust(directory):
        return ProjectRust(directory)
    else:
        raise errors.NotSupportedProject(directory)


def build_project(directory, options):
    directory = path.expanduser(directory)

    logger.info("build_project.directory: %s", directory)
    logger.info("build_project.debug: %s", options['debug'])

    guards.is_directory(directory)
    project = load_project(directory)
    project.build(options)
    logger.info("Build ran.")


def clean_project(directory):
    directory = path.expanduser(directory)
    guards.is_directory(directory)
    project = load_project(directory)
    project.clean()
    logger.info("Project cleaned.")


def get_projects_in_workspace(workspace):
    guards.is_directory(workspace)
    subfolders = utils.get_subfolders(workspace)
    projects = []

    for folder in subfolders:
        project_directory = path.join(workspace, folder)

        try:
            project = load_project(project_directory)
            projects.append(project)
        except Exception:
            pass

    return projects
