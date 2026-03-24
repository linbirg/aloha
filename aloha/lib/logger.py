import sys
import time
import os

import threading

default_encoding = 'utf-8'


class _thread_idx_map:
	def __init__(self):
		self.ident_list = []
		self.ident2idx = {}
		self.lock = threading.Lock()

	def get_idx(self, ident):
		with self.lock:
			i = self.ident2idx.get(ident)
			if i is None:
				self.ident_list.append(ident)
				i = len(self.ident_list) - 1
			self.ident2idx[ident] = i
			return i

	def idx2ident(self, idx):
		with self.lock:
			if idx < 0 or idx > len(self.ident_list) - 1:
				return None
			return self.ident_list[idx]


_th_idx_map = _thread_idx_map()


class _logger:
	class LocalData(threading.local):
		initialized = False

		def __init__(self, **kw):
			if self.initialized:
				raise SystemError('LocalData: __init__ called too many times')
			self.initialized = True
			#self.tid = threading.current_thread().ident
			self.tid = _th_idx_map.get_idx(threading.current_thread().ident)
			self.__dict__.update(kw)

	def __init__(self):
		self.LEVEL_ALL = 0

		self.LEVEL_DEBUG = 1
		self.LEVEL_TRACE = 2
		self.LEVEL_INFO = 3
		self.LEVEL_ANNOUNCE = 4
		self.LEVEL_WARNING = 5
		self.LEVEL_FATAL = 6

		self.LEVEL_NONE = 7

		self.level_info = (
			('!<', sys.stderr),
			('DEBUG', sys.stderr),
			('TRACE', sys.stderr),
			('INFO', sys.stderr),
			('ANNOUNCE', sys.stderr),
			('WARNING', sys.stderr),
			('FATAL', sys.stderr),
			('>!', sys.stderr),
		)

		self.LEVEL = dict([
			(v, i)
			for i, v in enumerate(('ALL', 'DEBUG', 'TRACE', 'INFO', 'ANNOUNCE',
							   'WARNING', 'FATAL', 'NONE'))
		])

		self.cur_trace_no = 0

		self.thread_local = None

		self.cur_output_level = 0

		# 使用 default_encoding
		self.encoding = default_encoding

	def set_log_file(self, std_file, greater_level_files=None, encoding=None):
		if greater_level_files is None:
			greater_level_files = {}
		if encoding is None:
			encoding = self.encoding
		self.encoding = encoding

		newinfo = []
		# 对greater_level_files按照日志级别排序
		greater_levels = sorted(greater_level_files.items(),key=lambda item: item[0])
		# 将标准输出文件作为最低级别的日志输出文件
		greater_levels.insert(0, (0, std_file))
		# 逐个处理日志文件，确保每个日志级别都有对应的文件
		next_greater_level = greater_levels.pop()
		for i in reversed(range(len(self.level_info))):
			while next_greater_level[0] > i:
				next_greater_level = greater_levels.pop()
			newinfo.append((self.level_info[i][0], next_greater_level[1]))

		#for i in range(self.LEVEL_NONE):
		#    newinfo.append((self.level_info[i][0], std_file))

		newinfo.reverse()
		self.level_info = tuple(newinfo)

		# debug_str = str(self.level_info)
		# print(debug_str)

	def set_trace_no(self, trace_no):
		if self.thread_local == None:
			self.cur_trace_no = trace_no
		else:
			self.thread_local.trace_no = trace_no

	def set_output_level(self, level):
		if isinstance(level, int) and level >= 0 and level <= self.LEVEL_NONE:
			self.cur_output_level = level
		elif isinstance(level, str) and level in self.LEVEL:
			self.cur_output_level = self.LEVEL[level]
		else:
			raise Exception('invalid log level:' + repr(level))

	def get_trace_no(self):
		return self.cur_trace_no if self.thread_local == None else self.thread_local.trace_no

	def get_tid(self):
		#return os.getpid() if self.thread_local == None else self.thread_local.tid
		return None if self.thread_local is None else self.thread_local.tid

	def get_ptid_str(self):
		return '%d.' % os.getpid() + ('' if self.thread_local == None else str(
			self.thread_local.tid))

	def set_multithread(self, enabled=True):
		if enabled:
			#self.thread_local = threading.local()
			#self.thread_init()
			self.thread_local = _logger.LocalData(trace_no=0)
			#print('[][][]ms: thread_local:%s, trace_no:%d, tid:%d' % (repr(self.thread_local), self.thread_local.trace_no, self.thread_local.tid))
		else:
			self.thread_local = None
			#print('[][][]ms: thread_local:%s, tid:%d' % (repr(self.thread_local), threading.current_thread().ident))

	def thread_init(self):
		self.thread_local.trace_no = 0
		self.thread_local.tid = threading.current_thread(
		).ident  # TODO: better change to thread_id.

	def _get_low_level_files(self, level):
		f_outs = []
		for t in self.level_info[:level+1]:
			if t[1] not in f_outs:
				f_outs.append(t[1])
		
		return f_outs

	# add by linbirg 20210715:输出日志文件，按照日志级别排序，高级别的日志会出现在所有低于其级别的输出文件中。低级别的只汇出现在低级别文件中。
	def log_output(self,
				   code_file,
				   code_func,
				   code_line,
				   level,
				   thetime,
				   msg,
				   trace_no=None):
		trace_no = self.get_trace_no() if trace_no is None else trace_no
		#tid = self.get_tid()
		ptid_str = self.get_ptid_str()
		# f_outs = self.level_info[level][1]
		f_outs = self._get_low_level_files(level)

		# print("f_outs:",f_outs)

		# if not isinstance(f_outs, list):
		# 	f_outs = [f_outs]

		#out_str = '[%s][%s:%d(%s)][%s:%.05f][%d][%d]%s\n' % \
		#        (self.level_info[level][0], code_file, code_line, code_func, \
		#         time.strftime('%Y%m%d %H:%M:%S', time.localtime(thetime)), thetime, tid, trace_no, msg)
		#out_str = '[%s][%s:%d(%s)][%s][%d][%d]%s\n' % \
		#        (self.level_info[level][0], code_file, code_line, code_func, \
		#         time.strftime('%Y%m%d %H:%M:%S', time.localtime(thetime)), tid, trace_no, msg)
		out_str = '[%s][%s:%d(%s)][%s][%s][%d]%s\n' % \
				(self.level_info[level][0], code_file, code_line, code_func, \
				 time.strftime('%Y%m%d %H:%M:%S', time.localtime(thetime)), ptid_str, trace_no, msg)

		# 使用 default_encoding 进行编码处理
		encoded_msg = out_str.encode(self.encoding, errors='replace')
		decoded_msg = encoded_msg.decode(self.encoding)

		for f_out in f_outs:
			try:
				f_out.write(decoded_msg)
				f_out.flush()
			except (OSError, IOError) as e:
				# 静默处理文件写入失败，避免日志写入失败导致主业务崩溃
				# 可选：输出到 stderr 作为后备
				try:
					sys.stderr.write(f'[logger] Write failed: {e}\n')
				except Exception:
					pass

	def _LOG_(self, level, msg, args, nframe=1):
		if level < self.cur_output_level:
			return
		if len(args) > 0:
			msg = msg % args
		fr = sys._getframe(nframe)
		filename = fr.f_code.co_filename
		filename = filename.replace('.py', '')
		funcname = fr.f_code.co_name
		lineno = fr.f_lineno
		tm = time.time()
		self.log_output(filename, funcname, lineno, level, tm, msg)


logger = _logger()


def get_logger() -> _logger:
	"""工厂函数：创建独立的 logger 实例，避免多项目配置冲突"""
	return _logger()


class _LoggerProxy:
	"""日志代理类：绑定到特定 logger 实例的便捷函数"""

	def __init__(self, log_instance: _logger):
		self._log = log_instance

	def DEBUG(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_DEBUG, msg, args, nframe=2)

	def TRACE(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_TRACE, msg, args, nframe=2)

	def INFO(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_INFO, msg, args, nframe=2)

	def ANNOUNCE(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_ANNOUNCE, msg, args, nframe=2)

	def WARNING(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_WARNING, msg, args, nframe=2)

	def FATAL(self, msg: str, *args):
		self._log._LOG_(self._log.LEVEL_FATAL, msg, args, nframe=2)


def create_logger(name: str | None = None) -> _LoggerProxy | _logger:
	"""创建带名称的 logger 实例或代理

	Args:
		name: 日志实例名称。如果为 None，返回基础 _logger 实例

	Returns:
		Logger 实例或代理对象
	"""
	if name:
		return _LoggerProxy(_logger())
	return _logger()


def log_output(code_file,
			   code_func,
			   code_line,
			   level,
			   thetime,
			   msg,
			   trace_no=None):
	global logger
	return logger.log_output(code_file, code_func, code_line, level, thetime,
							 msg, trace_no)


def _LOG_(level, msg, args, nframe=1):
	global logger
	return logger._LOG_(level, msg, args, nframe + 1)


def LOG_DEBUG(msg, *args):
	global logger
	logger._LOG_(logger.LEVEL_DEBUG, msg, args, nframe=2)


def LOG_TRACE(msg, *args):
	global logger
	logger._LOG_(logger.LEVEL_TRACE, msg, args, nframe=2)


def LOG_INFO(msg, *args):
	global logger
	logger._LOG_(logger.LEVEL_INFO, msg, args, nframe=2)


def LOG_ANNOUNCE(msg, *args):
	global logger
	logger._LOG_(logger.LEVEL_ANNOUNCE, msg, args, nframe=2)


def LOG_WARNING(msg, *args):
	global logger
	logger._LOG_(logger.LEVEL_WARNING, msg, args, nframe=2)


def LOG_FATAL(msg, *args):
	logger._LOG_(logger.LEVEL_FATAL, msg, args, nframe=2)
