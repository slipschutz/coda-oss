import os
from os.path import join, isdir, abspath, dirname
import Options
from Configure import ConfigurationError


def options(opt):
    opt.tool_options('java')
    opt.add_option('--disable-java', action='store_false', dest='java',
                   help='Disable java', default=True)
    opt.add_option('--with-java-home', action='store', dest='java_home',
                   help='Specify the location of the java home')
    opt.add_option('--require-java', action='store_true', dest='force_java',
               help='Require Java (configure option)', default=False)
    opt.add_option('--require-jni', action='store_true', dest='force_jni',
               help='Require Java lib/headers (configure option)', default=False)
    

def configure(self):
    if not Options.options.java:
        return
    
    from build import recursiveGlob
    
    if Options.options.java_home:
        self.environ['JAVA_HOME'] = Options.options.java_home 
    
    try:
        self.check_tool('java')
    except Exception, e:
        if Options.options.force_java:
            raise e
        else:
            return

    if not self.env.CC_NAME and not self.env.CXX_NAME:
        self.fatal('load a compiler first (gcc, g++, ..)')

    try:
        if not self.env.JAVA_HOME:
            self.fatal('set JAVA_HOME in the system environment')
    
        # jni requires the jvm
        javaHome = abspath(self.env['JAVA_HOME'][0])
        
        if not isdir(javaHome):
            self.fatal('could not find JAVA_HOME directory %r (see config.log)' % javaHome)
    
        incDir = abspath(join(javaHome, 'include'))
        if not isdir(incDir):
            self.fatal('could not find include directory in %r (see config.log)' % javaHome)
        
        incDirs = list(set(map(lambda x: dirname(x),
                      recursiveGlob(incDir, ['jni.h', 'jni_md.h']))))
        libDirs = list(set(map(lambda x: dirname(x),
                      recursiveGlob(javaHome, ['*jvm.a', '*jvm.lib']))))
        if not libDirs:
            libDirs = list(set(map(lambda x: dirname(x),
                          recursiveGlob(javaHome, ['*jvm.so', '*jvm.dll']))))
    
        if not self.check(header_name='jni.h', define_name='HAVE_JNI_H', lib='jvm',
                    libpath=libDirs, includes=incDirs, uselib_store='JAVA', uselib='JAVA',
                    function_name='JNI_GetCreatedJavaVMs'):
            if Options.options.force_jni:
                self.fatal('could not find lib jvm in %r (see config.log)' % libDirs)
    except ConfigurationError, ex:
        err = str(ex).strip()
        if err.startswith('error: '):
            err = err[7:]
        if Options.options.force_java:
            self.fatal(err)
        else:
            self.msg('Java lib/headers', err, color='YELLOW')