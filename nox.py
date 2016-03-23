def session_py27(session):
    session.interpreter = 'python2.7'


def session_test(session):
    session.install('ferrisnose')
    session.run('nosetests', '--with-ferris', 'ferris/tests')
