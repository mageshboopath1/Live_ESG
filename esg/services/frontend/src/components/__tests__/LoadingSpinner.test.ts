import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '../LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
  })

  it('renders with custom message', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        message: 'Loading data...'
      }
    })

    expect(wrapper.text()).toContain('Loading data...')
  })

  it('applies correct size class', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        size: 'lg'
      }
    })

    expect(wrapper.find('.spinner-lg').exists()).toBe(true)
  })

  it('renders fullscreen when prop is true', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        fullscreen: true
      }
    })

    expect(wrapper.find('.loading-fullscreen').exists()).toBe(true)
  })

  it('renders inline when fullscreen is false', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        fullscreen: false
      }
    })

    expect(wrapper.find('.loading-inline').exists()).toBe(true)
  })
})
