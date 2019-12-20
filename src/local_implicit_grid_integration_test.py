"""Integration Test for local_implicit_grid + PDELayer."""

# pylint: disable=import-error, no-member, too-many-arguments, no-self-use

import unittest
import numpy as np
import torch
from parameterized import parameterized
from local_implicit_grid import query_local_implicit_grid
from implicit_net import ImNet
from pde import PDELayer


class LocalImplicitGridIntegrationTest(unittest.TestCase):
    """Integration test for local_implicit_grid"""

    def test_local_implicit_grid_with_pde_layer(self):
        """integration test."""
        # setup parameters
        batch_size = 8  # batch size
        grid_res = 16  # grid resolution
        nc = 32  # number of latent channels
        dim_in = 3
        dim_out = 2
        n_filter = 16  # number of filters in neural net
        n_pts = 1024  # number of query points

        # setup pde constraints
        in_vars = 'x, y, t'  # matches dim_in
        out_vars = 'u, v'    # matches dim_out
        eqn_strs = ['dif(u, t) - (dif(dif(u, x), x) + dif(dif(u, y), y))',
                    'dif(v, t) - (dif(dif(v, x), x) + dif(dif(v, y), y))']
        eqn_names = ['diffusion_u', 'diffusion_v']

        # setup local implicit grid as forward function
        latent_grid = torch.rand(batch_size, grid_res, grid_res, grid_res, nc)
        query_pts = torch.rand(batch_size, n_pts, dim_in)
        model = ImNet(dim=dim_in, in_features=nc, out_features=dim_out, nf=n_filter)
        fwd_fn = lambda query_pts: query_local_implicit_grid(model, latent_grid, query_pts, 0., 1.)

        # setup pde layer
        pdel = PDELayer(in_vars=in_vars, out_vars=out_vars)
        for eqn_str, eqn_name in zip(eqn_strs, eqn_names):
            pdel.add_equation(eqn_str, eqn_name)
        pdel.update_forward_method(fwd_fn)
        val, res = pdel(query_pts)

        # it's harder to check values due to the randomness of the neural net. so we test shape
        # instead
        np.testing.assert_allclose(val.shape, [batch_size, n_pts, dim_out])
        for key in res.keys():
            res_value = res[key]
            np.testing.assert_allclose(res_value.shape, [batch_size, n_pts, 1])

if __name__ == '__main__':
    unittest.main()