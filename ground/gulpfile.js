var gulp = require('gulp'),
    babel = require('gulp-babel'),
    mocha = require('gulp-mocha'),
    sourcemaps = require('gulp-sourcemaps'),
    watch = require('gulp-watch');

const SRC_FILES = ['vg-*.js', '{lib,mock,test}/**/*.js'];
const ASSET_FILES = ['vg-console.sh', 'mock/*.jpg'];

gulp.task('babel', function() {
  return gulp.src(SRC_FILES, { base: '.' })
             .pipe(sourcemaps.init())
             .pipe(babel())
             .pipe(sourcemaps.write('.', { sourceRoot: __dirname }))
             .pipe(gulp.dest('dist'));
});

gulp.task('dist', function() {
  gulp.src(ASSET_FILES, { base: '.' })
      .pipe(gulp.dest('dist'));
});

gulp.task('test', ['babel'], function() {
  return gulp.src('dist/test/test-*.js')
             .pipe(babel())
             .pipe(mocha());
});

gulp.task('watch', function() {
  gulp.watch(SRC_FILES, ['test']);
});

gulp.task('default', ['babel', 'dist']);
