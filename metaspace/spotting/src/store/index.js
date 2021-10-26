import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import getters from './getters.js';
import mutations from './mutations.js';
import actions from './actions.js';

const store = new Vuex.Store({
  state: {
    // names of currently shown filters
    orderedActiveFilters: [],

    filterLists: null,
    filterListsLoading: false,

    // currently selected annotation
    annotation: undefined,

    // currently selected normalization matrix
    normalization: undefined,

    // is annotation table loading?
    tableIsLoading: true,

    lastUsedFilters: {},

    currentTour: null,

    currentUser: {}
  },

  getters,
  mutations,
  actions
})

export default store;
