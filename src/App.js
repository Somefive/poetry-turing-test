import './App.css';
import 'antd/dist/antd.css'
import { Input, message, Button } from 'antd'
import { UserOutlined, ArrowRightOutlined, RobotOutlined, LoadingOutlined } from '@ant-design/icons'
import { Component } from 'react'
import _ from 'lodash'
import poetries from './poetries.json'
import axios from 'axios'

// import Swiper core and required components
import SwiperCore, { Pagination, Scrollbar, A11y, Navigation } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

// Import Swiper styles
import 'swiper/swiper.scss';
import 'swiper/components/pagination/pagination.scss'
import 'swiper/components/navigation/navigation.scss'
import 'swiper/components/scrollbar/scrollbar.scss'

// install Swiper components
SwiperCore.use([Pagination, Scrollbar, A11y, Navigation]);

const API_HREF = process.env.PUBLIC_URL.replace('poetry-turing-test', 'api')

export default class App extends Component {
    constructor(props) {
      super(props)
      this.state = {
          model: 'login',
          username: '',
          score: 0,
          turingTests: [],
          mode: 'easy',
          countDown: 0,
          rank: 0,
          rankTotal: 0,
          guiding: 'firsttime',
          loading: false
      }
      this.poetries = _.shuffle(poetries)
      this.timer = undefined
      this.swiper = undefined
    }

    renderLogin() {
      const renderModeButton = (mode, color) => {
        return <Button onClick={() => this.setState({mode})} style={{
          color: mode === this.state.mode ? 'white' : 'black',
          background: mode === this.state.mode ? color : 'white',
          borderColor: color,
          borderRadius: 0,
          margin: '0.25em 0.75em'
        }}>{_.capitalize(mode)}</Button>
      }
      return (
        <div className="login">
          <div className="header">作诗图灵测试</div>
          <Input
            size="large"
            placeholder="请输入您的名字或昵称"
            prefix={<UserOutlined className="site-form-item-icon" />}
            suffix={
              <ArrowRightOutlined className="enter-btn" style={{color: this.state.username.length === 0 ? 'lightgray' : 'black'}} onClick={() => this.login()}/>
            }
            value={this.state.username}
            onChange={e => this.setState({username: e.target.value})}
            onPressEnter={() => this.login()}
          />
          <div className="mode-choice">
              {renderModeButton('easy', '#7cb305')}
              {renderModeButton('hard', '#cf1322')}
              {renderModeButton('lunatic', '#531dab')}
          </div>
          <div className="description">
            {this.state.mode === 'easy' && '在作诗图灵测试的Easy模式中，您将会被展现5组诗歌（包括标题、作者及内容），每组包括1首由诗人创作的诗歌和1首AI创作的诗歌，请选择您认为由人创作的诗歌。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'hard' && '在作诗图灵测试的Hard模式中，您将会被展现10组诗歌（包括标题及内容），每组包括1首由诗人创作的诗歌和2首AI创作的诗歌，请选择您认为由人创作的诗歌，每组回答限时1分钟。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'lunatic' && '在作诗图灵测试的Lunatic模式中，您将会被展现20组诗歌（仅包括诗歌内容），每组包括3首诗歌，其中至多包含1首由人创作的诗歌，请选择您认为由人创作的诗歌（若没有，则不选择），每组回答限时30秒。所有组选择完成后，您将会得知有多少组结果正确。'}
          </div>
        </div>
      )
    }

    login() {
      if (this.state.username.length === 0) message.warning('输入的名称不能为空')
      else {
        this.setState({loading: true})
        axios.get(`${API_HREF}/get-turing-tests/${this.state.mode}`).then(data => {
          const turingTests = data.data.tests.map((test, index) => { return {
            ...test, answer_id: '', index
          }})
          this.setState({model: 'poetry-turing-test', turingTests, loading: false})
        }).catch(err => {
          message.error(`${err}`)
          this.setState({loading: false})
        })
      }
    }

    renderScoreBoard() {
      return (
        <div className="score-board">
          <div className="header">
            <div>{this.state.username}</div>
            <div>您的得分是：<span className="user-score">{this.state.score}</span> / {this.state.turingTests.length}</div>
            <div>超越了<span className="user-rank">{(100 - this.state.rank * 100 / this.state.rankTotal).toFixed(2)}%</span>的人</div>
          </div>
          <div className="retry-btn"><Button size="large" onClick={() => this.setState({model: 'login'})}>再来一次</Button></div>
        </div>
      )
    }

    renderPoetry(poetry, parent) {
      const heightpercent = Math.floor(100 / parent.cases.length)
      const title = parent.title
      const author = parent.author
      const dynasty = parent.dynasty
      const content = poetry.content
      return (
        <div className={`poetry-card ${poetry.id === parent.answer_id ? 'selected': ''}`} onClick={() => {
          const tests = this.state.turingTests
          if (tests[parent.index].answer_id === poetry.id) tests[parent.index].answer_id = ''
          else tests[parent.index].answer_id = poetry.id
          let newState = {turingTests: tests}
          if (this.state.guiding === 'choosing') newState.guiding = 'goto-next'
          this.setState(newState)
        }} style={{
          height: `calc(${heightpercent}% - 1em)`
        }}>
          <div className="poetry-card-inner">
            {title && <div className="title">{title}</div>}
            {author && dynasty && <div className="author">{dynasty && dynasty + ' '}{author}</div>}
            {content && content.map((line, idx) => <div className="line" idx={idx}>{line}</div>)}
          </div>
        </div>
      )
    }

    renderPoetryTest(poetryTest) {
      return (
        <SwiperSlide key={poetryTest.index}>
          <div className="poetry-container">
            <div className="poetry-inner">
              {poetryTest && poetryTest.cases && poetryTest.cases.map(_case => this.renderPoetry(_case, poetryTest))}
            </div>
          </div>
        </SwiperSlide>
      )
    }

    submit() {
      if (this.state.mode === 'easy' && this.state.guiding !== '' && this.state.guiding !== 'submitting') return
      this.setState({loading: true})
      axios.post(`${API_HREF}/get-score`, {
        'username': this.state.username,
        'mode': this.state.mode,
        'answers': this.state.turingTests.map(test => { return {
          select_id: test.answer_id,
          options: test.cases.map(_case => _case.id)
        }})
      }).then(data => {
        const score = data.data.score
        const rank = data.data.rank
        const rankTotal = data.data.total
        let newState = {score, rank, rankTotal, model: 'score-board', loading: false}
        if (this.state.guiding === 'submitting') newState.guiding = 'finish'
        this.setState(newState)
      }).catch(err => {
        message.error(`${err}`)
        this.setState({loading: false})
      })
    }

    onSlideChange(reset) {
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = undefined
      }
      if (this.state.mode !== 'easy') {
        if (reset) {
          this.setState({countDown: this.state.mode === 'hard' ? 60 : 30})
        }
        this.timer = setTimeout(() => {
          if (this.state.countDown === 1) {
            if (this.swiper) {
              if (this.swiper.slides && this.swiper.realIndex === this.swiper.slides.length - 1) {
                this.submit()
              } else {
                this.swiper.slideNext()
              }
            }
          } else {
            this.setState({countDown: this.state.countDown - 1})
            this.onSlideChange(false)
          }
        }, 1000)
      } else if (this.state.guiding === 'swiping') {
        this.setState({guiding: 'click-submit'})
      }
    }

    renderPoetryTuringTest() {
      return (
        <div className="turing-test">
          <Swiper
            spaceBetween={50}
            slidesPerView={1}
            navigation={window.screen.width >= 720}
            pagination={{ clickable: true }}
            scrollbar={{ draggable: true }}
            onSlideChange={() => this.onSlideChange(true)}
            onSwiper={(swiper) => {
              this.swiper = swiper
              this.onSlideChange(true)
            }}
            allowSlidePrev={this.state.mode === 'easy'}
          >
            {this.state.turingTests.map(poetryTest => this.renderPoetryTest(poetryTest))}
          </Swiper>
          <div className="submit-btn">
            <Button type="primary" size="large" shape="circle" icon={<RobotOutlined />} onClick={() => this.submit()}/>
          </div>
        </div>
      )
    }

    renderTimer() {
      return (
        <div className="timer">
          <Button style={{borderColor: this.state.countDown <= 10 ? 'red' : 'darkgray'}} type="default" shape="circle">{(this.state.countDown >= 10 ? "" : " ") + `${this.state.countDown}`}</Button>
        </div>
      )
    }

    renderGuide() {
      return <div className="guide">
        {this.state.mode === 'easy' && ['', 'choosing', 'swiping', 'submitting'].indexOf(this.state.guiding) < 0 && <div className="guide-mask">
          <div className="guide-container">
            <div className="welcome">
              {this.state.guiding === 'firsttime' && 'Hi，欢迎参加作诗图灵测试。'}
              {this.state.guiding === 'make-choice' && '点击您认为是真实的诗人所作的诗。'}
              {this.state.guiding === 'choosing' && ''}
              {this.state.guiding === 'goto-next' && '向左滑动进入下一首。'}
              {this.state.guiding === 'swiping' && ''}
              {this.state.guiding === 'click-submit' && '继续进行剩下的答题，然后点击右下角的提交按钮完成测试。'}
              {this.state.guiding === 'submitting' && ''}
              {this.state.guiding === 'finish' && '恭喜您完成测试教程！现在您可以选择任一难度开始挑战。'}
            </div>
            <div className="skip">
              {this.state.guiding !== 'finish' && <Button className="btn next-btn" onClick={() => {
                let guiding = 'make-choice'
                if (this.state.guiding === 'make-choice') guiding = 'choosing'
                if (this.state.guiding === 'goto-next') guiding = 'swiping'
                if (this.state.guiding === 'click-submit') guiding = 'submitting'
                this.setState({guiding})
              }}>下一步</Button>}
              <Button className="btn skip-btn" style={{color: 'white', background: '#00474f', borderColor: '#00474f'}} onClick={() => this.setState({guiding: ''})}>
                {this.state.guiding === 'finish' ? '完成教程' : '跳过教程'}
              </Button>
            </div>
          </div>
        </div>}
      </div>
    }

    render() {
      return (
        <div className="App" style={{background: `url(${process.env.PUBLIC_URL}/background.jpg)`, backgroundSize: 'cover'}}>
          <div className="App-inner">
            {this.state.model === 'login' && this.renderLogin()}
            {this.state.model === 'poetry-turing-test' && this.renderPoetryTuringTest()}
            {this.state.model === 'score-board' && this.renderScoreBoard()}
            {this.state.model === 'poetry-turing-test' && this.state.mode !== 'easy' && this.renderTimer()}
          </div>
          {(this.state.model === 'poetry-turing-test' || this.state.model === 'score-board') && this.state.guiding !== '' && this.renderGuide()}
          {this.state.loading && <div className="loading-mask">
            <div className="mask-inner"><LoadingOutlined /></div>
          </div>}
        </div>
      )
    }
}