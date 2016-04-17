import fastqimagealigner
import logging
import nd2tools
import os

log = logging.getLogger(__name__)


def fast_possible_tile_keys(nd2, im_idx, min_tile, max_tile):
    _, _, _, _, _, _, cols = nd2tools.get_nd2_image_coord_info(nd2)
    cols.sort()
    pos_name = nd2tools.convert_nd2_coordinates(nd2, im_idx=im_idx, outfmt='pos_name')
    col_idx = cols.index(pos_name[1:])
    expected_tile = int(min_tile + col_idx * float(max_tile - min_tile)/(len(cols)-1))
    return tile_keys_given_nums(range(expected_tile - 1, expected_tile + 2))


def tile_keys_given_nums(tile_nums):
    return ['lane1tile{0}'.format(tile_num) for tile_num in tile_nums]


def process_fig(alignment_parameters, image, nd2_filename, tile_data, im_idx, objective, possible_tile_keys, experiment):
    for directory in (experiment.figure_directory, experiment.results_directory):
        full_directory = os.path.join(directory, nd2_filename)
        if not os.path.exists(full_directory):
            os.makedirs(full_directory)

    sexcat_fpath = os.path.join(nd2_filename.replace('.nd2', ''), '%d.cat' % im_idx)
    fic = fastqimagealigner.FastqImageAligner(experiment)
    fic.load_reads(tile_data)
    fic.set_image_data(im_idx, objective, image)
    fic.set_sexcat_from_file(sexcat_fpath)
    fic.rough_align(possible_tile_keys,
                    alignment_parameters.rotation_estimate,
                    alignment_parameters.fq_w_est,
                    snr_thresh=alignment_parameters.snr_threshold)
    return fic


def write_output(im_idx, fic, experiment, tile_data):
    intensity_fpath = os.path.join(experiment.results_directory, '{}_intensities.txt'.format(im_idx))
    stats_fpath = os.path.join(experiment.results_directory, '{}_stats.txt'.format(im_idx))
    all_read_rcs_filepath = os.path.join(experiment.results_directory, '{}_all_read_rcs.txt'.format(im_idx))
    fic.output_intensity_results(intensity_fpath)
    fic.write_alignment_stats(stats_fpath)

    ax = fic.plot_all_hits()
    ax.figure.savefig(os.path.join(experiment.figure_directory, '{}_all_hits.pdf'.format(im_idx)))
    del ax

    ax = fic.plot_hit_hists()
    ax.figure.savefig(os.path.join(experiment.figure_directory, '{}_hit_hists.pdf'.format(im_idx)))
    del ax

    all_fic = fastqimagealigner.FastqImageAligner(experiment)
    all_fic.all_reads_fic_from_aligned_fic(fic, tile_data)
    all_fic.write_read_names_rcs(all_read_rcs_filepath)
    del all_fic
