// This file is automatically generated from ethereum_networks.c.mako
// DO NOT EDIT

#include "ethereum_networks.h"
#include "ethereum.h"

#define NETWORKS_COUNT 7

static const EthereumNetworkInfo networks[NETWORKS_COUNT] = {
    {
        .chain_id = 1,
        .slip44 = 60,
        .symbol = "ETH", /* Ethereum */
        .name = "",
    },
    {
        .chain_id = 3,
        .slip44 = 1,
        .symbol = "tETH", /* Ropsten */
        .name = "",
    },
    {
        .chain_id = 4,
        .slip44 = 1,
        .symbol = "tETH", /* Rinkeby */
        .name = "",
    },
    {
        .chain_id = 5,
        .slip44 = 1,
        .symbol = "tETH", /* Görli */
        .name = "",
    },
    {
        .chain_id = 56,
        .slip44 = 714,
        .symbol = "BNB", /* Binance Smart Chain */
        .name = "",
    },
    {
        .chain_id = 61,
        .slip44 = 61,
        .symbol = "ETC", /* Ethereum Classic */
        .name = "",
    },
    {
        .chain_id = 137,
        .slip44 = 966,
        .symbol = "MATIC", /* Polygon */
        .name = "",
    },
};

const EthereumNetworkInfo UNKNOWN_NETWORK = {
    .chain_id = CHAIN_ID_UNKNOWN,
    .slip44 = SLIP44_UNKNOWN,
    .symbol = "UNKN",
    .name = "",
};

const EthereumNetworkInfo *ethereum_get_network_by_chain_id(uint64_t chain_id) {
  for (size_t i = 0; i < NETWORKS_COUNT; i++) {
    if (networks[i].chain_id == chain_id) {
      return &networks[i];
    }
  }
  return &UNKNOWN_NETWORK;
}

const EthereumNetworkInfo *ethereum_get_network_by_slip44(uint32_t slip44) {
  for (size_t i = 0; i < NETWORKS_COUNT; i++) {
    if (networks[i].slip44 == slip44) {
      return &networks[i];
    }
  }
  return &UNKNOWN_NETWORK;
}

bool is_unknown_network(const EthereumNetworkInfo *network) {
  return network->chain_id == CHAIN_ID_UNKNOWN;
}
bool is_ethereum_slip44(uint32_t slip44) {
  for (size_t i = 0; i < NETWORKS_COUNT; i++) {
    if (networks[i].slip44 == slip44) {
      return true;
    }
  }
  return false;
}

int32_t ethereum_slip44_by_chain_id(uint64_t chain_id) {
  for (size_t i = 0; i < NETWORKS_COUNT; i++) {
    if (networks[i].chain_id == chain_id) {
      return networks[i].slip44;
    }
  }
  return SLIP44_UNKNOWN;
}