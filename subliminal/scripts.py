#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2012 Antoine Bertin <diaoulael@gmail.com>
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
import argparse
import datetime
import logging
import os
import re
import subliminal
import sys


def main():
    parser = argparse.ArgumentParser(description='Subtitles, faster than your thoughts')
    parser.add_argument('-l', '--language', action='append', dest='languages', help='wanted language (ISO 639-1)', metavar='LG')
    parser.add_argument('-s', '--service', action='append', dest='services', help='service to use (%s)' % ', '.join(subliminal.core.filter_services(subliminal.SERVICES)), metavar='NAME')
    parser.add_argument('-m', '--multi', action='store_true', help='download multiple subtitle languages')
    parser.add_argument('-f', '--force', action='store_true', help='replace existing subtitle file')
    parser.add_argument('-w', '--workers', action='store', help='use N threads (default: %(default)s)', metavar='N', type=int, default=4)
    parser.add_argument('-a', '--age', action='store', help='scan only for files newer or older (prefix with +) than AGE (e.g. 12h, 1w2d, +3d6h)', metavar='AGE', default=None)
    group_verbosity = parser.add_mutually_exclusive_group()
    group_verbosity.add_argument('-q', '--quiet', action='store_true', help='disable output')
    group_verbosity.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    group_cache = parser.add_mutually_exclusive_group()
    group_cache.add_argument('--cache-dir', action='store', dest='cache_dir', help='cache directory to use', metavar='DIR', default=os.path.expanduser('~/.config/subliminal'))
    group_cache.add_argument('--no-cache-dir', action='store_false', dest='cache_dir', help='do not use cache directory (some services may not work)')
    parser.add_argument('--version', action='version', version=subliminal.__version__)
    parser.add_argument('paths', nargs='+', help='path to video file or folder', metavar='PATH')
    args = parser.parse_args()

    # Set log verbosity
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(asctime)s %(name)-24s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    elif not args.quiet:
        logging.basicConfig(level=logging.WARN, format='%(levelname)s: %(name)s %(message)s')

    # Create cache directory
    if not os.path.exists(args.cache_dir):
        os.mkdir(args.cache_dir)

    # Create filter function
    scan_filter = None
    if args.age:
        regex = re.compile(r'^(?P<sign>\+?)((?P<weeks>\d+?)w)?((?P<days>\d+?)d)?((?P<hours>\d+?)h)?')
        parts = regex.match(args.age)
        if not parts:
            raise ValueError('Incorrect age format')
        time_params = {}
        parts = parts.groupdict()
        for name, param in parts.iteritems():
            if param and name != 'sign':
                time_params[name] = int(param)
        if parts['sign'] == '+':
            scan_filter = lambda x: datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(x)) < datetime.timedelta(**time_params)
        else:
            scan_filter = lambda x: datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(x)) > datetime.timedelta(**time_params)

    # Convert paths to unicode
    paths = [unicode(x, sys.stdin.encoding) for x in args.paths]

    # Download subtitles
    with subliminal.Pool(args.workers) as p:
        results = p.download_subtitles(paths, languages=args.languages, services=args.services, cache_dir=args.cache_dir,
                                       force=args.force, multi=args.multi, scan_filter=scan_filter)

    if not results:
        if not args.quiet:
            sys.stderr.write('No subtitles downloaded\n')
        exit(1)
    if not args.quiet:
        print '*' * 50
        print 'Downloaded %d subtitle(s) for %d video(s)' % (sum([len(s) for s in results.itervalues()]), len(results))
        for _, subtitles in results.iteritems():
            for subtitle in subtitles:
                print '%s from %s' % (subtitle.path, subtitle.service)
        print '*' * 50


if __name__ == '__main__':
    main()
