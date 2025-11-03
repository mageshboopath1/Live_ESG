<template>
  <footer class="bg-white border-t border-gray-200 mt-auto">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- About Section -->
        <div>
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
            About
          </h3>
          <p class="text-sm text-gray-600">
            ESG Intelligence Platform provides transparent ESG analysis through automated
            document processing and AI-powered indicator extraction.
          </p>
        </div>

        <!-- Quick Links -->
        <div>
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
            Quick Links
          </h3>
          <ul class="space-y-2">
            <li>
              <router-link to="/" class="text-sm text-gray-600 hover:text-gray-900">
                Home
              </router-link>
            </li>
            <li>
              <router-link to="/comparison" class="text-sm text-gray-600 hover:text-gray-900">
                Compare Companies
              </router-link>
            </li>
          </ul>
        </div>

        <!-- Info -->
        <div>
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
            Information
          </h3>
          <p class="text-sm text-gray-600">
            Data sourced from BRSR Core framework and company sustainability reports.
          </p>
        </div>
      </div>

      <div class="mt-8 pt-8 border-t border-gray-200">
        <p class="text-sm text-gray-500 text-center">
          © {{ currentYear }} ESG Intelligence Platform. All rights reserved.
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>
