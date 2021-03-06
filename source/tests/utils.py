import subprocess, re, os, shutil
import os.path as op
from datetime import datetime


COMMAND_W_DT = '{NOW\+(.*)}'
NOW = datetime.now()


def parse_trace(trace_file, get_datetime):
	sequence = []
	command, out = None, None
	for line in trace_file:
		if line.startswith('$ '):
			if command is not None:
				sequence.append((command, out))
			command = line[2:-1]
			match = re.search(COMMAND_W_DT, command)
			if match is not None:
				delay = match.group(1)
				dt = get_datetime(delay)
				dt_string = dt.strftime('%Y-%m-%d')
				command = re.sub(COMMAND_W_DT, dt_string, command)
			out = ''
		else:
			out += line
	sequence.append((command, out))
	return sequence


def test_trace(filename, get_datetime, print_commands=False):
	with open(filename) as trace_file:
		sequence = parse_trace(trace_file, get_datetime)
	errors = {'crash': 0, 'clash': 0}
	for command, out in sequence:
		if print_commands:
			print(command)
		process = subprocess.Popen(command, shell=True,
			universal_newlines=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		status = process.returncode
		try:
			assert status == 0
			assert stderr == ''
		except AssertionError:
			print('[cRash] >', command)
			print('[stderr]:\n'+stderr)
			errors['crash'] += 1
		try:
			assert out == stdout
		except AssertionError:
			print('[cLash]', command)
			print('[output]:\n'+stdout)
			print('[expected]:\n'+out)
			errors['clash'] += 1
	return errors



def backup_and_replace(source, replacement=None):
	is_loc = op.exists(source)
	backup_path = None
	if is_loc:
		backup_path = source + '-backup-' + str(NOW.timestamp())
		shutil.copy(source, backup_path)
	if replacement is not None:
		shutil.copy(replacement, source)
	else:
		if is_loc:
			os.remove(source)
	return backup_path
