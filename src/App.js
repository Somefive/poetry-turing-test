import './App.css';
import 'antd/dist/antd.css'
import { Input, message, Button, Table } from 'antd'
import { UserOutlined, ArrowRightOutlined, RobotOutlined, LoadingOutlined, MailOutlined } from '@ant-design/icons'
import { Component } from 'react'
import _ from 'lodash'
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

const API_HREF = (process.env.NODE_ENV === 'production') ? process.env.PUBLIC_URL.replace('poetry-turing-test', 'api') : 'http://localhost:19544' //'http://localhost:19545' //'https://turing-poet.aminer.cn/api/'

export default class App extends Component {
    constructor(props) {
      super(props)
      this.state = {
          model: 'login',
          username: localStorage.getItem('v2.username') || '',
          turingTests: [],
          mode: 'easy',
          countDown: 0,
          guiding: 'firsttime',
          loading: false,
          config: {},
          session_id: '',
          session_key: '',
          results: {},
          email: localStorage.getItem('v2.email') || '',
          rankBoard: {}
      }
      this.timecosts = []
      this.microTimer = undefined
      this.timer = undefined
      this.swiper = undefined
      this.rankBoardContainer = undefined
    }

    renderLogin() {
      const renderModeButton = (mode, color) => {
        return <Button onClick={() => this.setState({mode})} style={{
          color: mode === this.state.mode ? 'white' : 'black',
          background: mode === this.state.mode ? color : 'white',
          borderColor: color,
          borderRadius: 0,
          margin: '0.25em 0.75em',
          width: '6em'
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
          <div className="mode-choice">
            {renderModeButton('extra', '#780650')}
          </div>
          <div className="description">
            {this.state.mode === 'easy' && '在作诗图灵测试的Easy模式中，您将会被展现5组诗歌（包括标题、作者及内容），每组包括1首由诗人创作的诗歌和1首AI创作的诗歌，请选择您认为由人创作的诗歌。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'hard' && '在作诗图灵测试的Hard模式中，您将会被展现10组诗歌（包括标题及内容），每组包括1首由诗人创作的诗歌和2首AI创作的诗歌，请选择您认为由人创作的诗歌，每组回答限时60(绝句)/90(律诗)秒。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'lunatic' && '在作诗图灵测试的Lunatic模式中，您将会被展现20组诗歌（仅包括诗歌内容），每组包括3首诗歌，其中至多包含1首由人创作的诗歌，请选择您认为由人创作的诗歌（若没有，则不选择），每组回答限时30(绝句)/45(律诗)秒。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'extra' && '在作诗图灵测试的Extra模式中，您将会被展现20组诗歌（包括标题、作者及内容），每组包括3首诗歌，其中包含1首由人创作的诗歌和2首由不同AI创作的诗歌，请选择您认为由人创作的诗歌，每组回答不限时。所有组选择完成后，您将会得知有多少组结果正确。'}
          </div>
        </div>
      )
    }

    login() {
      if (this.state.username.length === 0) message.warning('输入的名称不能为空')
      else {
        localStorage.setItem('v2.username', this.state.username)
        this.setState({loading: true})
        axios.post(`${API_HREF}/get-turing-tests`, {mode: this.state.mode, username: this.state.username}).then(data => {
          const turingTests = data.data.tests.map((test, index) => { return {
            ...test, answer_id: '', index, time: 0
          }})
          this.setState({
            model: 'poetry-turing-test',
            turingTests,
            loading: false,
            session_id: data.data.session_id,
            session_key: data.data.session_key,
            config: data.data.config
          })
          this.timecosts = turingTests.map(_ => 0)
          this.microTimer = setInterval(() => {
            if (this.swiper) this.timecosts[this.swiper.realIndex] += 100
          }, 100)
        }).catch(err => {
          message.error(`${err}`)
          this.setState({loading: false})
        })
      }
    }

    checkRank() {
      const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      if (!re.test(this.state.email.toLowerCase())) {
        message.error(`请输入正确的邮箱格式`)
        return
      } else {
        localStorage.setItem('v2.email', this.state.email)
        this.setState({loading: true})
        axios.post(`${API_HREF}/get-user-rank`, {
          'username': this.state.username,
          'mode': this.state.mode,
          'session_id': this.state.session_id,
          'session_key': this.state.session_key,
          'email': this.state.email
        }).then(data => {
          this.setState({rankBoard: data.data, loading: false, model: 'rank-board'})
        }).catch(err => {
          message.error(`${err}`)
          this.setState({loading: false})
        })
      }
    }

    renderRankBoard() {
      const renderCol = (text, record) => {
        let background = 'white'
        let color = record.rank === 3 ? 'white' : 'black'
        if (record.rank === 1) background = 'gold'
        else if (record.rank === 2) background = 'silver'
        else if (record.rank === 3) background = '#cd7f32'
        return {
          props: {
            style: {
              color, background,
              fontWeight: record.rank === userrank ? 'bold' : 'normal'
            }
          },
          children: <div>{text}</div>
        };
      }
      const userrank = this.state.rankBoard.userrank
      const columns = [
        {
          title: '排名',
          dataIndex: 'rank',
          key: 'rank',
          width: 80,
          align: 'center',
          render: renderCol
        },
        {
          title: '用户',
          dataIndex: 'username',
          key: 'username',
          width: 160,
          align: 'center',
          ellipsis: true,
          render: renderCol
        },
        {
          title: '分数',
          dataIndex: 'score',
          key: 'score',
          width: 80,
          align: 'center',
          render: renderCol
        },
        {
          title: '用时(秒)',
          dataIndex: 'timecost',
          key: 'timecost',
          width: 120,
          align: 'center',
          render: renderCol
        },
        {
          title: '日期',
          dataIndex: 'date',
          key: 'date',
          width: 120,
          align: 'center',
          render: renderCol
        }
      ]
      const dataSource = this.state.rankBoard.ranks.map(row => { return {
        key: row[0], rank: row[0], username: row[1], score: row[2], timecost: row[3] < 10000 ? row[3].toFixed(1) : 'NA', date: row[4] < '2022' ? row[4].replace('T', ' ').slice(5, row[4].length - 3) : 'NA'
      }})
      const width = columns.reduce((p, x) => p + x.width, 0)
      return (
        <div className="rank-board" ref={e => { this.rankBoardContainer = e }}>
          <div className="top-info">排行榜</div>
          <div className="header-info">您当前在<span className="mode-text">{this.state.mode}</span>模式的排名是{userrank}。</div>
          <Table dataSource={dataSource} columns={columns} scroll={{x: width}}/>
          <div className="retry-btn"><Button size="large" onClick={() => this.setState({model: 'login'})}>返回</Button></div>
        </div>
      )
    }

    renderScoreBoard() {
      const results = this.state.results
      return (
        <div className="score-board">
          <div className="header">
            <div>{this.state.username}</div>
            <div>您的得分是：<span className="user-score">{results.score}</span> / {this.state.config.num_testcases}</div>
            <div>耗时{results.timecost.toFixed(1)}秒</div>
            <div>您的最好成绩是：<span className="user-score">{results.best_record[0]}</span></div>
            {results.best_record[1] < 10000 && <div>耗时{results.best_record[1].toFixed(1)}秒</div>}
            <div>排名：<span className="user-score">{results.rank}</span> / {results.total} </div>
            <div>超越了<span className="user-rank">{(100 - results.rank * 100 / results.total).toFixed(2)}%</span>的人</div>
          </div>
          <div className="retry-btn"><Button size="large" onClick={() => this.setState({model: 'login'})}>再来一次</Button></div>
          <Input
            className="email-input"
            size="large"
            placeholder="输入邮箱查看排行榜"
            prefix={<MailOutlined className="site-form-item-icon" />}
            suffix={
              <ArrowRightOutlined className="enter-btn" style={{color: this.state.email.length === 0 ? 'lightgray' : 'black'}} onClick={() => this.checkRank()}/>
            }
            value={this.state.email}
            onChange={e => this.setState({email: e.target.value})}
            onPressEnter={() => this.checkRank()}
          />
        </div>
      )
    }

    renderPoetry(choice, test) {
      const heightpercent = Math.floor(100 / this.state.config.num_options)
      const title = test.title
      const author = test.author
      const dynasty = test.dynasty
      const content = choice.content
      return (
        <div className={`poetry-card ${choice.id === test.answer_id ? 'selected': ''}`} onClick={() => {
          const tests = this.state.turingTests
          if (tests[test.index].answer_id === choice.id) tests[test.index].answer_id = ''
          else tests[test.index].answer_id = choice.id
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
              {poetryTest && poetryTest.choices.map(choice => this.renderPoetry(choice, poetryTest))}
            </div>
          </div>
        </SwiperSlide>
      )
    }

    submit() {
      clearInterval(this.microTimer)
      if (this.state.mode === 'easy' && this.state.guiding !== '' && this.state.guiding !== 'submitting') return
      this.setState({loading: true})
      axios.post(`${API_HREF}/get-score`, {
        'username': this.state.username,
        'mode': this.state.mode,
        'session_id': this.state.session_id,
        'session_key': this.state.session_key,
        'answers': this.state.turingTests.map((test, idx) => { return {
          select_id: test.answer_id,
          options: test.choices.map(_case => _case.id),
          time: this.timecosts[idx] / 1000
        }})
      }).then(data => {
        let newState = {results: data.data, model: 'score-board', loading: false}
        if (this.state.guiding === 'submitting') newState.guiding = 'finish'
        this.setState(newState)
      }).catch(err => {
        message.error(`${err}`)
        this.setState({loading: false})
      })
    }

    onSlideChange(reset) {
      if (this.state.model !== 'poetry-turing-test') return
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = undefined
      }
      if (this.state.config.base_timelimit) {
        if (reset) {
          let countDown = this.state.config.base_timelimit
          if (this.state.turingTests[this.swiper.realIndex].scheme[0] > 2 && this.state.config.timelimit_boost) countDown *= this.state.config.timelimit_boost
          this.setState({countDown: Math.round(countDown)})
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
            allowSlidePrev={this.state.config.allow_backward}
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
            {this.state.model === 'poetry-turing-test' && this.state.config.base_timelimit && this.renderTimer()}
          </div>
          {(this.state.model === 'poetry-turing-test' || this.state.model === 'score-board') && this.state.guiding !== '' && this.renderGuide()}
          {this.state.loading && <div className="loading-mask">
            <div className="mask-inner"><LoadingOutlined /></div>
          </div>}
          {this.state.model === 'rank-board' && this.renderRankBoard()}
        </div>
      )
    }
}