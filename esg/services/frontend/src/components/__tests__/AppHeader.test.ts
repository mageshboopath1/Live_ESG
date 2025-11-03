import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import AppHeader from '../AppHeader.vue'

describe('AppHeader', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/comparison', name: 'comparison', component: { template: '<div>Comparison</div>' } }
    ]
  })

  it('renders the logo and brand name', () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('ESG')
    expect(wrapper.text()).toContain('ESG Intelligence')
  })

  it('renders navigation links', () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router]
      }
    })

    const links = wrapper.findAll('a')
    expect(links.length).toBeGreaterThan(0)
  })

  it('toggles mobile menu when button is clicked', async () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router]
      }
    })

    const mobileMenuButton = wrapper.find('button[aria-label="Toggle menu"]')
    expect(mobileMenuButton.exists()).toBe(true)

    // Initially mobile menu should be closed
    expect(wrapper.vm.mobileMenuOpen).toBe(false)

    // Click to open
    await mobileMenuButton.trigger('click')
    expect(wrapper.vm.mobileMenuOpen).toBe(true)

    // Click to close
    await mobileMenuButton.trigger('click')
    expect(wrapper.vm.mobileMenuOpen).toBe(false)
  })
})
