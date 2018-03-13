from pybuilder.core import use_plugin, init, Author, task
from pybuilder.pluginhelper.external_command import ExternalCommandBuilder
from pybuilder.utils import read_file
import json

use_plugin('python.core')
use_plugin('python.unittest')
use_plugin('python.install_dependencies')
use_plugin('python.flake8')
use_plugin('python.coverage')
use_plugin('python.distutils')
use_plugin('filter_resources')

name = 'sqlserver'
authors = [
    Author('Charles Knox', 'charles.m.knox@gmail.com')
]
summary = 'pyodbc sqlserver python helper classes'
url = 'https://github.com/charles-m-knox/pyodbc-sqlserver'
version = '0.0.1'
default_task = [
    'clean',
    'analyze',
    'cyclomatic_complexity',
    'package'
]


@init
def set_properties(project):
    project.set_property('unittest_module_glob', 'test_*.py')

    project.set_property('coverage_break_build', False)

    project.set_property('flake8_max_line_length', 120)
    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_break_build', True)
    project.set_property('flake8_include_scripts', True)
    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_ignore', 'E501')

    project.get_property('filter_resources_glob').extend([
        '**/sqlserver/*'])  # needed otherwise tests and stuff won't work

    project.build_depends_on_requirements('requirements-build.txt')

    project.depends_on_requirements('requirements.txt')


@task('cyclomatic_complexity', description='calculates and publishes cyclomatic complexity')
def cyclomatic_complexity(project, logger):

    command = ExternalCommandBuilder('radon', project)
    command.use_argument('cc')
    command.use_argument('-a')

    result = command.run_on_production_source_files(logger)

    # count_of_warnings = len(result.report_lines)
    if len(result.error_report_lines) > 0:
        logger.error('Errors while running radon, see {0}'.format(result.error_report_file))

    for line in result.report_lines[:-1]:
        logger.debug(line.strip())

    average_complexity_line = result.report_lines[-1].strip()
    logger.info(average_complexity_line)

    # publish cyclomatic complexity
    print(get_value(average_complexity_line))


def _coverage_file(project):
    return project.expand_path('$dir_reports/{0}'.format('coverage.json'))


def get_value(line):
    if ':' in line:
        return line.split(':')[1].strip()


@task('publish_coverage', description='publishes overall coverage')
def publish_coverage(project, logger):

    coverage_file = _coverage_file(project)
    coverage_json = read_file(coverage_file)
    coverage = json.loads(''.join(coverage_json))['overall_coverage']
    logger.info('Overall coverage: {0}'.format(coverage))
